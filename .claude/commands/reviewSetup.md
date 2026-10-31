# /reviewSetup

Review the candidate setup and summarize what the workspace currently records about the user. This command is read-only: do not edit files or fill gaps by guessing.

## Read

Read the current contents of:

- `CLAUDE.md` (Candidate Profile section)
- `.claude/skills/job-application-assistant/01-candidate-profile.md`
- `.claude/skills/job-application-assistant/02-behavioral-profile.md`
- `.claude/skills/job-application-assistant/04-job-evaluation.md`
- `.claude/skills/job-scraper/search-queries.md`

Use the candidate profile and preferences as the source of truth. The evaluation framework and search queries show how those preferences are currently translated into job-fit and search behavior.
Treat bracketed template tokens and instructional examples as **Missing**, not as
candidate information. A preference is **Explicit** only when a profile source records
it as user-provided; do not promote an agent's inference to an explicit preference.

## Report

Summarize:

1. Target roles, functions, seniority, and desired responsibilities.
2. Preferred sectors, target companies, and company criteria (including companies or environments to avoid).
3. Location, commute, remote/hybrid/on-site, and travel preferences.
4. Salary expectation or floor, including currency and period when recorded.
5. Work eligibility, languages, employment type, and other job constraints relevant to filtering.
6. Motivations, preferred environment, and any additional context the user supplied.
7. Whether the evaluation framework and search-query file reflect those preferences.

For each category, label information as one of:

- **Explicit** — directly recorded by the user or stated in a profile source.
- **Inferred** — a cautious interpretation; explain the evidence and do not present it as confirmed.
- **Missing** — not recorded or still a placeholder.
- **Inconsistent** — sources disagree; quote or identify both values and ask the user which is correct.

Distinguish a missing value from an explicit “no preference.” Do not infer a salary, commute, company preference, or job constraint from location, prior roles, or market norms.

End with a short list of corrections or missing details the user may want to provide. Tell them they can use `/alterSetup` to propose updates, then run `/reviewSetup` again to verify them. Do not make changes during this command.
