# /automate - Hands-off apply loop that stops at every submit button

You are orchestrating a batch application loop. For the top-ranked unapplied jobs you
produce tailored CVs and cover letters, open each employer's form, fill every grounded
field, upload both PDFs, and **stop one click short of submit** on each one before
moving to the next. The user comes back to a batch of parked applications in
`pending_submit.md` and clicks Submit themselves.

**This command never submits.** The refuse-list in
`.claude/skills/venki-application-agent/SKILL.md` ("Human-only actions") is load-bearing
and applies identically in automation mode. The `/automate` flag is not permission to
submit; it is permission to prepare up to the submit button.

Follow these steps **exactly in order**.

**Standing rule — write new facts back to the profile.** Same as `/apply` (see
`apply.md` top). A fact that surfaces during a batch run and lives only in chat will be
stripped from the next session's drafts as a fabrication. If something comes up for one
job that is really a profile-level correction, pause the loop long enough to write it
to `01-candidate-profile.md` in the same turn.

---

## Step 0: Parse arguments and guard rails

`$ARGUMENTS` is a flag string. Parse these tokens (order-independent):

| Flag | Default | Meaning |
|---|---|---|
| `--max-jobs N` | `5` | How many jobs to prep this run. Hard cap `20`; reject higher. |
| `--skip-scrape` | off | Reuse the current `job_scraper/seen_jobs.json`; do not run `/scrape`. |
| `--skip-rank` | off | Reuse existing `rank_verdict` values; do not run the ranker. |
| `--dry-run` | off | Compile and verify CV + cover letter per job but do **not** open the browser. Tracker rows stay at `drafted`; `pending_submit.md` is not written. |
| `--min-score N` | `70` | Lower bound on `rank_score` for a job to enter the batch. The ranker's "strong" threshold from `04-job-evaluation.md` is the authoritative source — read it and use that value if it disagrees with `70`. |

Reject unknown flags with a one-line error.

**Preflight guards (abort the whole run on any failure):**

1. **Profile populated.** If `CLAUDE.md` contains any `[PLACEHOLDER]` token (grep for
   `\[[A-Z_]+\]`), abort with: *"CLAUDE.md still has placeholder tokens. Run `/setup`
   first — automated applications will not be sent out from a placeholder profile."*
   The guard also catches `[YOUR_NAME]`, `[YOUR_CITY]`, etc. — those are the same
   pattern.
2. **Master resume present.** `cv/main_example_improved.tex` must exist (same precondition
   as `/apply` Step 2). Abort with the same instruction to run `/setup`.
3. **Tracker header sane.** If `job_search_tracker.csv` exists, read its header. If the
   header is malformed or missing `company`/`role`/`status`, stop before touching it
   and report the problem. (Same guard `/status` applies.)
4. **Browser tools available for a non-`--dry-run` run.** Confirm the Playwright MCP
   browser capabilities named by `venki-application-agent/SKILL.md` are exposed. If any
   are missing, either switch to `--dry-run` and tell the user, or abort — do not
   claim success without a real browser.

---

## Step 1: Scrape (optional)

Unless `--skip-scrape` is set, invoke the `scrape` skill in unattended mode. The skill's
own unattended contract (`SKILL.md:51-70`) forbids `AskUserQuestion`, searches every
configured role and location, writes new entries to `job_scraper/seen_jobs.json` via
`tools/scrape_state.py store`, and ends with a status report rather than a question.
Pass it `--unattended` so it stays in that mode throughout.

Capture the status report. If zero new entries landed in `seen_jobs.json`, continue
anyway — a previous `/scrape` may have populated it, and `--skip-rank` + an existing
backlog is a valid run shape.

---

## Step 2: Rank (optional)

Unless `--skip-rank` is set, score every entry in `seen_jobs.json` whose `status` is
`new` or whose `rank_verdict` is missing/stale. Dispatch the `posting-scorer` agent
(`subagent_type: posting-scorer`, `.claude/agents/posting-scorer.md`) in batches of up
to 10 entries per call; pass the compact rubric from `04-job-evaluation.md`. The agent
returns strict JSON (`{strengths, gaps, guard, status: scored|expired|unreachable}` per
job). Apply its JSON back via:

```bash
python tools/rank_state.py apply --input "${SCRATCHPAD:?}/scored.json"
```

(Windows note: `python`, not `python3`. The pathways in `.claude/settings.json` allow
both.) The `apply` subcommand writes `rank_score`, `rank_verdict`, `rank_date`,
`language_gate`, `language_note`, `strengths`, `gaps`, `guard` back into each entry's
record in `seen_jobs.json`.

---

## Step 3: Select the batch

Read `seen_jobs.json` and `job_search_tracker.csv`. An entry is a batch candidate when
**all** of the following hold:

- `rank_verdict == "strong"` and `rank_score >= --min-score`
- `status ∉ {drafted, prepped, applied, acknowledged, assessment, interviewing, offer, hired, rejected, offer_declined, withdrawn, expired}` in `seen_jobs.json` **and** no tracker row for the same company+role carries one of those statuses. The tracker-side check is **batched, not per-job**: write the candidates as a JSON array of `{title, company, url}` to the scratchpad, then run

  ```bash
  python tools/applied_check.py --results "${SCRATCHPAD:?}/candidates.json" --json
  ```

  It returns `{"clear": [...], "collisions": [...], "clear_count", "collision_count"}`; keep only `clear`. Its normalization strips LinkedIn's `" in <loc>"` decoration and legal-form suffixes, so it catches a role already applied to through a different portal — which plain URL dedup misses.
- `language_gate != "fail"` (if the ranker set a Language Gate verdict)
- `deadline` is either absent or `>= today` (no expired postings)
- The URL host passes `/apply` Step 1 "Source Host Verification" into category 1, 2, or 3 — an unverified host is not auto-approved for a batch run; dropped here with a line in the end-of-run report explaining why.

Sort surviving candidates by `rank_score` descending. Take the top `--max-jobs`. If
fewer than `--max-jobs` survive, run with however many did and name the number in the
end-of-run summary — never pad with weaker candidates.

**Show the batch to the user with a single up-front approval prompt:**

> "I'm about to prepare N applications: [company — role (score)]... × N. Each one
> runs the full `/apply` verification (reviewer agent, PDF compile, ATS text-layer
> extraction) and then parks at the submit screen in the browser. **I will not click
> Submit on any of them** — you'll do that yourself from `pending_submit.md` after the
> loop. Proceed?"

Wait for a yes. **This is the only interactive gate in the loop.** No per-job prompts
after this point. If the user says no, stop here with no state changes.

---

## Step 4: Loop body (sequential, one job at a time)

**Never parallelize.** The Playwright MCP browser session is shared and will race or
deadlock if two jobs try to drive it at once.

For each selected candidate in rank-sorted order:

1. **Dispatch `/apply` in batch mode.** Invoke `/apply <url> --batch` (and `--dry-run`
   too, if that flag is set on `/automate`). The `--batch` flag — defined in
   `apply.md:21` and honored at Step 1 and Approval Gate 2 — tells `/apply` to:
   - skip the Step 1 "proceed with drafting?" prompt (use the rank verdict instead;
     abort this one job if the live Step 0.5 liveness check fails or the posting-guard
     ⚠-flags, same as today);
   - skip the Approval Gate 2 "form preparation?" prompt;
   - still run every verification step without exception (reviewer agent, lualatex /
     xelatex compile, `verify_pdf.py` page count, `verify_layout.py`, ATS text-layer
     extract). Safety does not get skipped in batch mode.
   - still write the tracker row via Step 6b as `drafted`.

2. **If `--dry-run` is set,** stop here for this job. Status stays `drafted`.
   Continue to the next candidate.

3. **Otherwise, dispatch `venki-application-agent` with `--automate`.** Compute the
   canonical job key:

   ```bash
   python tools/job_key.py make_key --company "<company>" --title "<role>" --url "<url>"
   ```

   Invoke the skill with that key, the verified application URL, and the absolute paths
   to the tailored CV and cover letter. The skill's "Automation mode" section
   (`venki-application-agent/SKILL.md`, "Automation mode (`--automate` arg)") requires
   it to end its reply with exactly one fenced ```AUTOMATE_RESULT``` JSON block.

4. **Parse the `AUTOMATE_RESULT` block.** Extract the first fenced
   ```AUTOMATE_RESULT``` block in the skill's reply and `json.loads` it. On parse
   failure or missing block: mark this job as `error` in the per-run log, keep the
   tracker row at `drafted`, continue to the next job. Do not promote to `prepped`.

5. **Update the tracker row** only when `at_submit_button == true`:
   - `status` → `prepped`
   - `notes` → append `prepped_date=<today>; form_url=<form_url>; blocked=<n>` (where `<n>` is `len(blocked_fields)`)
   - Leave `date`, `cv_file`, `cover_letter_file`, `source`, `deadline` as `/apply`
     wrote them.
   - When `at_submit_button == false`: append to `notes`
     `[<today>] automate_blocked; reason=<first blocked_fields[].reason or "unknown">`.
     Keep `status` at `drafted`.

6. **Log one JSONL line** to `logs/automate_<ISO8601>.jsonl` (same timestamp as the
   start of this `/automate` run; create `logs/` if absent):

   ```json
   {"job_key": "...", "url": "...", "verdict": "strong", "prep_status": "prepped|drafted|error", "blocked_fields": [...], "uploaded_paths": [...]}
   ```

7. **On any uncaught exception** inside this candidate: catch it. Write a log line
   with `prep_status: "error"` and `error: "<message>"`. Mark the tracker row
   `error` in `notes`. Continue to the next candidate — never abort the whole loop
   because one job broke.

---

## Step 5: Write pending_submit.md

Fresh file at repo root (overwrite any prior one; the per-run log in `logs/` is the
durable record). Skip this step if `--dry-run` is set.

Format: one `##` section per `prepped` job this run. Each section:

```markdown
## <Company> — <Role> (rank_score)

- **Open form:** <form_url>
- **CV:** [<path>](<path>)
- **Cover letter:** [<path>](<path>)
- **Fit score:** <rank_score>

### Fields that need your eyes before Submit

- `<field label>` — <reason> (first `blocked_fields[]` from `AUTOMATE_RESULT`)
- ...

### Prefilled values to confirm

- `<field label>` (from `needs_user_review`)
- ...

### Fields filled in

<small, collapsible-looking list of `answered_fields` grouped by section — just field: value lines>

---
```

End the file with:

```markdown
# How to use this file

For each section above: open the form URL, confirm the "needs your eyes" fields,
spot-check the filled fields, then click Submit yourself. After each one, update the
tracker row from `prepped` to `applied` via `/status` or by hand — `/automate` will
not touch it.
```

---

## Step 6: End-of-run summary

Print, in this order:

- `N candidates in seen_jobs.json after Step 3 filter; selected top K = min(N, --max-jobs).`
- `Drafted: X. Prepped: Y. Errored: E.` (With names of the errored jobs if any.)
- `Review file: pending_submit.md` (if not `--dry-run`).
- `Per-run log: logs/automate_<ISO8601>.jsonl`.
- `Next: open pending_submit.md, click Submit on each, then run /status or /apply follow-up to move each tracker row from prepped to applied.`

Do **not** declare any application submitted. Do **not** write `applied` to any tracker
row from `/automate`. That transition is `/status`'s job after the user confirms the
submit click.

---

## Design invariants (do not relax)

- **Zero per-job interactive gates during the loop.** The one up-front batch approval
  in Step 3 is the only prompt. If a per-job prompt would otherwise fire, the loop
  logs and skips rather than asks.
- **`venki-application-agent` never clicks Submit.** The refuse-list in
  `venki-application-agent/SKILL.md` applies identically in `--automate` mode. If a
  future reader of this file wants to add a `--really-submit` flag, they must first
  propose the change to that skill's "Human-only actions" section — and the correct
  answer there is still no.
- **One tool, one key.** All dedup across scrape / rank / apply / automate goes
  through `tools/job_key.py:make_key`. Never invent a parallel key.
- **Sequential only.** No parallel browser tabs; no `Promise.all` on `/apply` calls.
- **CLAUDE.md must be populated.** The Step 0 placeholder guard is a hard abort, not a
  warning. Applications are the user's reputation leaving the house; a placeholder
  profile has no business reaching an employer.
