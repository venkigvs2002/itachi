# /alterSetup

Update the candidate's job-search setup from the additional information or corrections they provide. Use this for preferences and facts that should persist beyond the current conversation.

## Read and plan

Read the relevant current values before proposing edits:

- `CLAUDE.md` (Candidate Profile section)
- `.claude/skills/job-application-assistant/01-candidate-profile.md`
- `.claude/skills/job-application-assistant/02-behavioral-profile.md`
- `.claude/skills/job-application-assistant/04-job-evaluation.md`
- `.claude/skills/job-scraper/search-queries.md`

Classify each user statement as a factual correction, a new fact, a preference, or a request that does not belong in the persistent profile. Do not turn an inference into a fact. Ask a focused question if the requested change is ambiguous or conflicts with another recorded value.

Map confirmed updates to the smallest relevant set of files:

| Information | Update |
|---|---|
| Identity, education, work history, skills, languages, work eligibility | `01-candidate-profile.md` and the matching `CLAUDE.md` section; update other factual source documents only when they contain the contradicted value |
| Target roles, seniority, desired responsibilities, sectors, motivations | Candidate preferences in `01-candidate-profile.md` and the matching `CLAUDE.md` sections (including Target Sectors); relevant criteria in `04-job-evaluation.md` and role queries in `search-queries.md` |
| Location, commute, remote/hybrid/on-site, travel | Candidate preferences in `01-candidate-profile.md` and `CLAUDE.md`; location criteria in `04-job-evaluation.md` and `search-queries.md` |
| Salary floor or target | Candidate preferences in `01-candidate-profile.md` and `CLAUDE.md`; salary guidance in `04-job-evaluation.md` when relevant. Never put personal salary expectations into public search queries or application documents unless the user explicitly asks |
| Target/avoided companies, sectors, or company criteria | Candidate preferences in `01-candidate-profile.md` and `CLAUDE.md`; company criteria in `04-job-evaluation.md` and employer targeting in `search-queries.md` |
| Behavioral preferences or additional context | The matching section of `02-behavioral-profile.md` or `01-candidate-profile.md`, and `CLAUDE.md` when it is a durable job-search preference |
| Deal-breakers | `01-candidate-profile.md` preferences and `CLAUDE.md`'s Deal-breakers section; also update evaluation gates only when the user confirms a hard constraint |

For each planned edit, show the proposed value and the file(s) to change. Preserve unrelated content and existing structure. Do not copy private details into CV templates, search queries, or application artifacts unless the user explicitly requests it.

## Confirm and apply

Before editing, present a concise change list and ask the user to confirm it. If they decline or revise it, do not apply the unconfirmed version. After confirmation, make surgical edits and keep the relevant sources consistent. Do not change unrelated scoring rules, portal settings, or search configuration.

If a value is explicitly unknown or the user has no preference, record that distinction rather than inventing a value. If a changed preference affects search behavior, update the matching location/role/company criteria in `search-queries.md`; do not change unrelated query categories.

## Verify

Re-read the edited sections and report:

- What changed and in which files.
- Any unresolved source conflicts or missing values.
- Whether a preference was propagated to evaluation and search criteria.

Finish with an updated `/reviewSetup`-style summary based on the saved files. Do not claim that a change was saved unless it was verified on disk.
