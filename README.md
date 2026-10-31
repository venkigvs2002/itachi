# Itachi

A complete agent setup for job hunting, built on [Claude Code](https://claude.com/claude-code).

Itachi turns a job search into a pipeline: it finds postings, scores them against your
real profile, writes a tailored CV and cover letter for each one, verifies the PDFs
actually render correctly and parse through an ATS, fills the employer's application
form, and then **stops and hands you the submit button.**

It never submits an application on your behalf. That is the one line it will not cross,
and it is enforced in several places on purpose.

---

## What it does

| Command | What it does |
|---|---|
| `/setup` | One-time onboarding. Builds your profile from documents you drop in `documents/`, a single CV, or an interview. Populates everything else. |
| `/reviewSetup` | Read-only summary of what the workspace currently knows about you, labelled Explicit / Inferred / Missing. |
| `/alterSetup` | Surgical corrections to your profile and preferences. |
| `/scrape` | Searches installed job portals plus search-engine-indexed boards. Deduplicates across runs. |
| `/apply <url>` | The core workflow. Verifies the posting is live, scores fit, drafts CV + cover letter, runs a reviewer agent over them, compiles and inspects the PDFs, records the application. |
| `/automate` | Batch mode. Runs `/apply` across the top-ranked jobs, fills each employer form, parks at the submit screen, moves on. One approval up front, none per job. |
| `/nightly` | The unattended runner. Scrape → rank → draft → bundle → emailed report. No browser, no forms. |
| `/schedule-nightly` | Registers `/nightly` on a cron schedule. |
| `/status` | Reviews tracked applications; optionally checks for employer replies via read-only Gmail. |

## The part that matters most

**Nothing gets submitted without you.** Four independent mechanisms keep it that way:

1. `venki-application-agent` — the only component that touches a browser form — carries
   a refuse-list that includes *"never click a final submit/apply/complete action."* It
   also refuses passwords, terms acceptance, and CAPTCHA/MFA solving.
2. That refuse-list applies identically in automation mode. The `--automate` flag is
   explicitly not a submit authorization.
3. The tracker has a dedicated `prepped` status meaning "form filled, waiting for your
   click." It is never promoted to `applied` by any automated path — only by you
   confirming you submitted.
4. `/nightly` cannot reach the browser at all. Unattended form-filling at midnight with
   nobody watching is a deliberate non-feature.

If you are reading this thinking "I'll just add a `--really-submit` flag," read
`.claude/skills/venki-application-agent/SKILL.md` first. The answer there is still no,
and the reasons are written down.

## Other things it refuses to do

- **Fabricate.** Every claim in a draft is audited against three sources: your profile
  file, your master resume, and `CLAUDE.md`. An ungrounded claim gets stripped. A genuine
  skills gap is acknowledged honestly in the cover letter rather than hidden — keyword
  stuffing is explicitly forbidden.
- **Trust a job posting.** Postings are third-party input and are treated as data, never
  instructions. `tools/posting_guard.py` strips hidden text, invisible styling and
  instruction-shaped lines before anything reads a posting, and flags what it removed.
  Links found *inside* a posting body are never fetched.
- **Draft from a dead listing.** `/apply` re-verifies at the employer's own careers site
  or official ATS on every run. A cached page, a tracker row, or a previous scrape is not
  evidence a job is still open.
- **Ship a broken PDF.** Compiling is not enough. Every document is rendered, visually
  inspected, page-counted, checked for orphaned entry titles and whitespace holes, and
  its text layer extracted to confirm an ATS parser sees clean text with a real email and
  phone number.

## Layout

```
.claude/
  commands/     8 slash commands (the table above)
  skills/
    job-application-assistant/   10 modules: profile, behavioral, writing style,
                                 evaluation, CV + cover templates, interview prep,
                                 forms, web research, status taxonomy
    job-scraper/                 portal search + dedup, has an unattended mode
    venki-application-agent/     browser form prep; stops before submit
  agents/       3 read-only subagents (cannot write files by design):
                application-reviewer, posting-fetcher, posting-scorer
  settings.json permission allow/ask/deny lists

.agents/skills/ portal search CLIs (bun/TypeScript)
                enabled: linkedin-search, freehire-search
                opt-in:  jobindex, jobnet, jobbank, jobdanmark (Danish market)

tools/          18 Python helpers. Notable ones:
                job_key.py       canonical dedup key — the only key producer
                posting_guard.py untrusted-input gate
                verify_pdf.py    page count + ATS text-layer extraction
                verify_layout.py whitespace holes, orphaned headings
                applied_check.py normalized duplicate-application check
                bundle_drafts.py zips a run's drafts

cv/             LaTeX CVs (moderncv/banking). main_example_improved.tex is the
                master, generated by /setup.
cover_letters/  LaTeX cover letters (cover.cls, needs xelatex) — created by /setup
documents/      intake for /setup; per-application posting archives
CLAUDE.md       your profile + the verification checklist
```

Generated at runtime: `job_search_tracker.csv`, `job_scraper/seen_jobs.json`,
`company_research/`, `reports/`, `logs/`, `pending_submit.md`.

## Getting started

```bash
# 1. Install the portal CLIs (needs bun)
python tools/install_portal_clis.py

# 2. Build your profile — do this before anything else
/setup

# 3. Sanity-check what it recorded
/reviewSetup

# 4. Apply to something
/apply https://example.com/jobs/12345
```

**`/setup` is not optional.** Until it runs, `CLAUDE.md` is a template full of
`[PLACEHOLDER]` tokens and there is no master resume, so `/apply`, `/automate` and
`/nightly` will all refuse to run. That refusal is deliberate — a placeholder profile has
no business reaching an employer.

### Requirements

- Claude Code
- A LaTeX distribution with **lualatex** (CVs) and **xelatex** (cover letters). MiKTeX or
  TeX Live. `pdflatex` is not sufficient — it fails on `fontawesome5` font expansion.
- `bun` for the portal search CLIs
- Python 3 with `pypdf` (`pip install pypdf`) for ATS text-layer extraction. Poppler's
  `pdftotext` works as a fallback.

On Windows use `python`, not `python3` — a python.org install ships no `python3`, so that
name reaches the Microsoft Store alias and either exits silently or starts a different
interpreter without your packages.

## A note on your data

`CLAUDE.md` and the files under `.claude/skills/job-application-assistant/` hold your real
name, location, contact details, work history, salary expectations and behavioral profile.
Your CVs hold the same. **Keep this repository private.** If you fork or share it, strip
the profile first — `/setup` will rebuild it for whoever clones it.

Nothing here phones home. The agent fetches job postings and researches employers over
the public web; it writes only to this working directory.

## Known rough edges

- `/outcome` and `/rank` are referenced in a few places but have no command files.
  Ranking is implemented inline inside `/automate` and `/nightly`.
- `/schedule-nightly` registers through a session-scoped scheduler: the job is held in
  memory, dies when you close Claude Code, and expires after 7 days. A durable cloud
  routine is possible but needs this workspace pushed to a remote first.
- `/status`'s Gmail scan requires interactive per-run authorization, so it cannot run from
  a scheduled session. `/nightly` computes its tracker summary from the CSV instead.
- The Danish portal CLIs ship disabled. If your market is elsewhere, either enable the
  relevant ones in `.agents/skills/*/SKILL.md` or add a portal for your region.

---

Named after a character who did a great deal of unpleasant work quietly and in advance so
that someone else got to make the final choice. Seemed apt.
