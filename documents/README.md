# `documents/`

Two unrelated jobs live in this folder. **Intake** (what you drop here for `/setup` to
read) and **archive** (what `/apply` writes here per application). The naming rule at
the bottom is referenced by `/apply` and the application-assistant skill and is the
reason this file has to exist.

## Intake — what you put here

`/setup` Path A reads this tree and builds your profile from real source material
rather than an interview. Drop whatever you have; every subfolder is optional and
`/setup` reports what it found per folder.

| Subfolder | What goes in it |
|---|---|
| `cv/` | Existing CVs or résumés, any format. The richest single signal. |
| `linkedin/` | Your LinkedIn data export, or a saved copy of your profile. |
| `diplomas/` | Degree certificates, transcripts, course completions. |
| `references/` | Reference letters, recommendations, performance reviews. |
| `projects/` | Project write-ups, portfolio pieces, published work. |
| `applications/` | **Written by `/apply`, not by you.** See below. |

Re-running `/setup` Path A after adding more files is safe: it reads before writing and
will not re-propose a change already in your profile.

## Archive — what `/apply` writes here

`/apply` Step 6b archives each application's posting to:

```
documents/applications/<company>_<role>/job_posting.md
```

The file holds the posting text as `tools/posting_guard.py` cleaned it, verbatim, plus
a `## posting_guard` section with the gate's verdict and finding **counts** only —
never the flagged excerpts, so content the gate stripped is never re-read by a later
`/interview`, `/outcome` or `/setup` run.

An existing `job_posting.md` is left alone rather than overwritten when you apply to the
same company and role again.

## Subfolder naming

`<company>_<role>` — used for the archive folder above, and for the `cv/main_*` and
`cover_letters/cover_*` filenames — is **not** hand-assembled from the raw company and
role strings. Derive it by calling the canonical key helper:

```bash
python tools/job_key.py --company "<company>" --title "<role>" --url "<source url>"
```

It prints one line: the name to use. Pass the `url` when you have it.

Use that helper rather than writing your own slug. It handles the cases that have
actually caused damage:

- **Path characters cannot split the name across directories.** Everything outside
  `[a-z0-9]` becomes `-`, so `Acme Corp / EMEA` + `Senior AppSec Engineer, Platform`
  yields `acme-corp-emea_senior-appsec-engineer-platform` — one folder, not three.
- **Length is capped deterministically** (40 chars company, 60 role) with a short
  SHA-1 suffix appended when truncation kicks in, so two runs cannot cut the same long
  title at different points and produce two folders for one job.
- **Non-Latin scripts keep an identity.** A Cyrillic or CJK name ASCII-folds to an
  empty slug; the helper substitutes a hash (and the posting's numeric ID from the URL
  when one is present) instead of emitting a bare `company_` prefix.
- **Empty input still yields a name** (`unknown-company_untitled-<hash>`). The helper
  never returns an empty string, so the "stop before creating any file if the derived
  name is empty" branch in
  `.claude/skills/job-application-assistant/SKILL.md` is a guard against a helper
  failure, not an expected path. If it ever does fire, stop — do not invent a fallback
  name, because a wrong name silently splits one application's files across two
  folders.

Derive the name **once** per application and reuse that exact value for the CV, the
cover letter, and the archive path. Deriving it twice from slightly different company
or role strings is how the three files end up disagreeing.
