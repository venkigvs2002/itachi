# /nightly - Non-interactive nightly job search (scrape, rank, draft, report)

You are running the unattended nightly pipeline. Scrape the configured boards, rank what
came back, draft tailored documents for the top matches, bundle them, write a report, and
email it. Then stop.

**This command never opens a browser, never fills a form, and never submits anything.**
Form preparation stays in interactive `/automate`, where a human is awake to watch it.
`/nightly` stops at compiled, verified documents on disk.

**This command never prompts.** It is fired by a scheduler into a fresh session with
nobody watching. Every failure path writes the reason into the report and exits cleanly.
A `/nightly` run that blocks on a question is a silent failure: the schedule looks healthy,
the user gets no email, and nothing reveals the problem until they go looking. If you
reach a point where you would normally ask, record it in the report and move on.

Arguments in `$ARGUMENTS`:

| Flag | Default | Meaning |
|---|---|---|
| `--max-drafts N` | `3` | How many top-ranked jobs to draft documents for. Hard cap `10`. Drafting is the expensive leg — a reviewer agent plus two LaTeX compiles per job. |
| `--min-score N` | from `04-job-evaluation.md` | Lower bound on `rank_score` to be drafted. |
| `--email ADDR` | none | Where to send the report. When absent, write the report to disk and say in the summary that no address was supplied. |
| `--no-email` | off | Write the report to disk only. |
| `--scrape-only` | off | Stop after Step 2. Useful for a cheap nightly that only refreshes the pipeline. |

---

## Step 0: Preflight (never prompt; report and exit on failure)

Run every check below. Collect **all** failures rather than stopping at the first, so one
report names everything that needs fixing.

1. **Profile populated.** Grep `CLAUDE.md` for `\[[A-Z_]+\]`. Any match is a failure;
   record the count.
2. **Master resume present.** `cv/main_example_improved.tex` must exist.
3. **Search queries configured.** Read `.claude/skills/job-scraper/search-queries.md`.
   It must have at least one target role family and at least one location that is not
   `[Not specified]`. An unconfigured query file means the scrape searches nothing —
   `search-queries.md` forbids guessing a role or location to fill the gap.
4. **Cover-letter assets.** `cover_letters/` and its `cover.cls` must exist, or cover
   letters cannot compile. If missing, continue in CV-only mode and say so in the report
   rather than failing the whole run.
5. **Tracker header sane.** If `job_search_tracker.csv` exists, its header must carry
   `company`, `role`, `status`. A malformed header is a failure — never rewrite it.
6. **Naming rule reachable.** `documents/README.md` must exist; `/apply` derives
   `<company>_<role>` from its Subfolder naming rule via `tools/job_key.py`.

**On any failure in 1, 2, 3, 5 or 6:** write `reports/job_search_<YYYY-MM-DD>.md` with a
`## Run aborted at preflight` section naming each failed check and the fix (for 1-3 the
fix is `/setup`), email it if an address was supplied, and exit. Do not scrape, do not
draft.

---

## Step 1: Scrape (unattended)

Invoke the `scrape` skill with `--unattended`. Its unattended contract forbids
`AskUserQuestion`, requires it to search every configured role and location rather than
the usual top-three limit, and requires it to end with a report rather than a question.

Keep the skill's end-of-run report text — its `### Source coverage` block goes into the
nightly report verbatim, so the user can see which boards were searched, which were
unavailable, and which failed.

The skill writes `job_scraper/seen_jobs.json` through `python tools/scrape_state.py store`.
Do not write that file by any other route.

If the scrape returns zero new postings, that is a normal outcome, not a failure — carry
on to Step 6 and report it.

---

## Step 2: Rank (inline)

**Do not call `/rank`. There is no such command.** Rank inline, exactly as
`automate.md` Step 2 does:

1. Select entries in `seen_jobs.json` whose `status` is `new` or whose `rank_verdict` is
   missing.
2. Dispatch the `posting-scorer` agent (`subagent_type: posting-scorer`) in batches of at
   most 10 entries, passing the compact rubric from
   `.claude/skills/job-application-assistant/04-job-evaluation.md`.
3. Write the agent's JSON to the scratchpad and apply it:

   ```bash
   python tools/rank_state.py apply --input "${SCRATCHPAD:?}/scored.json"
   ```

   (Windows: `python`, not `python3`.)

If `--scrape-only` was passed, skip to Step 6 now.

---

## Step 3: Select

Read `seen_jobs.json` and `job_search_tracker.csv`. Keep an entry when all hold:

- `rank_verdict == "strong"` and `rank_score >= --min-score`
- No tracker row for the same company+role carries a blocking status. This check is
  **batched, not per-job**: write the surviving candidates as a JSON array of
  `{title, company, url}` objects to the scratchpad, then run

  ```bash
  python tools/applied_check.py --results "${SCRATCHPAD:?}/candidates.json" --json
  ```

  It returns `{"clear": [...], "collisions": [...], "clear_count", "collision_count"}`.
  Keep only the `clear` entries; name each collision in the report with its
  `tracker_status` and `tracker_date`. The normalization is why this matters — it
  matches LinkedIn's decorated `"OakNorth in India"` against a tracker row for
  `"OakNorth"`, which plain URL dedup misses.
- `language_gate != "fail"`
- `deadline` absent, or on/after today
- The URL host classifies into category 1, 2 or 3 of `/apply` Step 1's Source Host
  Verification. An unverified host is never drafted unattended; drop it and name it in
  the report.

Sort by `rank_score` descending, take the top `--max-drafts`. Fewer surviving than the cap
is fine — report the number and never pad with weaker matches.

---

## Step 4: Draft (per job, sequential)

For each selected job, invoke:

```
/apply <url> --batch --dry-run
```

`--batch` skips `/apply`'s two interactive gates (the Step 1 fit prompt and Approval
Gate 2). `--dry-run` stops it before Step 7, so no browser opens. Every verification step
still runs: the `application-reviewer` agent, both compiles, `verify_pdf.py` page counts,
`verify_layout.py`, and the ATS text-layer extraction. Verification is not what gets
skipped in an unattended run.

`/apply` writes the tracker row itself at `drafted`. **Leave it there.** `prepped` is set
only by an interactive `/automate` run that actually filled a form; `/nightly` must never
write it.

On an exception, a failed compile that will not converge, a Dead or Unverified liveness
verdict, or a ⚠ posting-guard verdict: record the job and the reason, and continue to the
next one. One bad posting never aborts the run.

---

## Step 5: Bundle

Collect the CV and cover letter paths `/apply` reported for each drafted job and zip them:

```bash
python tools/bundle_drafts.py \
  --file "cv/main_<company>_<role>.pdf"            --group "<company>_<role>" \
  --file "cover_letters/cover_<company>_<role>.pdf" --group "<company>_<role>" \
  --out "reports/bundle_<YYYY-MM-DD>.zip"
```

Repeat the `--file`/`--group` pair per document; `--group` keeps each job's two documents
together inside the zip. Derive `<company>_<role>` with `tools/job_key.py` per
`documents/README.md`, never by hand. The helper skips missing files with a warning and
exits 1 when nothing could be bundled — treat that as "no zip this run," not a run failure.

Bundle the **PDFs**, not the `.tex` sources: the PDF is what an employer reads and what
the user would attach.

---

## Step 6: Tracker summary (read-only)

Compute the summary statistics directly from `job_search_tracker.csv`, following the
"Summary calculations" rules in
`.claude/skills/job-application-assistant/10-application-status.md`: total submitted
(excluding `drafted`, `prepped` and `expired`), responses, interviews, pending, and
waiting time from `applied_date`.

**Do not invoke `/status`, and do not touch Gmail for a status scan.** `/status` gates its
Gmail scan on an interactive per-run authorization with no flag or stored-consent escape
hatch. A scheduled session cannot answer that question, and a scheduled prompt that tells
`/status` it is authorized would be the scheduler manufacturing the user's consent. Read
the tracker, compute the numbers, move on.

Flag follow-up cues per that file's thresholds (8-14 days: consider following up; over 14:
long wait). Never infer a rejection from silence.

---

## Step 7: Write the report

Write `reports/job_search_<YYYY-MM-DD>.md`, creating `reports/` if absent. Structure it
like `pending_submit.md` — that is the established per-run digest format in this repo:

```markdown
# Job search - <YYYY-MM-DD>

<N> new postings found, <M> ranked strong, <K> drafted, <E> errored.

## Matches

| Fit | Role | Company | Location | Deadline | Apply |
|-----|------|---------|----------|----------|-------|
| 86  | ...  | ...     | ...      | ...      | [link](...) |

## Drafted

### <Company> - <Role> (score)
- **CV:** [path](path)
- **Cover letter:** [path](path)
- **Posting:** <url>
- **Why it scored well:** <strengths from the ranker>
- **Gaps acknowledged:** <gaps from the ranker>

## Bundle

`reports/bundle_<YYYY-MM-DD>.zip`

## Tracker summary

<the read-only numbers from Step 6, plus any follow-up cues>

## Source coverage

<the scraper's own coverage block from Step 1, verbatim>

## Problems this run

<dropped hosts, failed compiles, dead postings, skipped checks - or "none">
```

Then append the standing footer:

```markdown
---
Nothing here has been submitted. To apply: review a drafted pair, then run
`/automate --skip-scrape --skip-rank --max-jobs 1` while you are at the keyboard to fill
the form, or open the posting and apply by hand.
```

---

## Step 8: Email the report

Unless `--no-email` is set or no address was supplied, send the report with
`mcp__claude_ai_Gmail__send_message`:

- **To:** the address from `--email` and nothing else.
- **Subject:** `Job search - <YYYY-MM-DD> - <N> matches, <K> drafted`
- **Body:** the report markdown from Step 7, with the zip path named in it.

This is a deliberate, scoped exception to this workspace's standing read-only-Gmail
convention, taken because the user chose email delivery for the nightly report. Keep it
inside these lines:

- One message per run, to the user's own confirmed address only.
- The body is the generated report. Nothing else.
- Never send to, cc, or reply to an employer, a recruiter, or any third party.
- Never send an application, a CV, or a cover letter to an employer. The attachments
  stay on disk; the email names their paths.
- Never read mail here. Step 6 already ruled out the Gmail status scan.

If the send fails, say so in the final summary and leave the report on disk — the file is
the durable artifact, the email is a convenience.

---

## Step 9: Log

Append one JSONL line per processed job to `logs/nightly_<ISO8601>.jsonl` (same timestamp
for the whole run; create `logs/` if absent), reusing the shape `/automate` established:

```json
{"job_key": "...", "url": "...", "score": 86, "verdict": "strong", "draft_status": "drafted|skipped|error", "cv": "...", "cover": "...", "error": null}
```

Finish with a short plain-text summary to the transcript: counts, the report path, the zip
path, whether the email went out. Do not end with a question.

---

## Invariants

- **No browser. No forms. No submission.** Not reachable from this command at all.
- **No prompts.** Every branch either proceeds or records and exits.
- **Never writes `prepped`.** That status means a form was filled, which `/nightly` cannot do.
- **Never fakes `/status`'s Gmail consent.**
- **One key helper.** All naming and dedup goes through `tools/job_key.py`.
- **Sequential drafting.** No parallel `/apply` dispatch.
