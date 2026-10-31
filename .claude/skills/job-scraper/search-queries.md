# Search Queries for Job Scraper

<!-- SETUP: Populate role families, skills, locations, and target companies from explicit user preferences. -->

## Candidate-specific search configuration

<!-- /setup populates these fields. "Not specified" must remain explicit rather than guessed. -->

- **Target markets/countries:** [Not specified]
- **Target role families and title variants:** [Not specified]
- **Target locations:** [Not specified]
- **Remote / hybrid / onsite preferences:** [Not specified]
- **Key profile-backed search skills:** [Not specified]
- **Target companies (up to 10 prioritized):** [Not specified]
- **Professional search languages:** [Not specified]
- **Approved adjacent role families:** [Not specified]

## Search scope and source rules

`/scrape` searches all applicable sources for the candidate's configured role families
and target locations. A source may be searched through an installed portal CLI, through
WebSearch with a `site:` query, or both when the CLI provides useful structured coverage
and indexed coverage is a worthwhile supplement.

Search-engine results are discovery leads, not proof that a listing is live, complete,
or still accepting applications. Do not scrape portals outside their documented CLI.
Do not claim a board was searched if its source was unavailable, disabled, not applicable,
or deferred; report that state in the coverage summary.

### Installed portal CLIs

`/scrape` discovers every `.agents/skills/*/SKILL.md` and runs enabled CLIs using their
documented flags. Current examples include:

- Country-agnostic: `linkedin-search`, `freehire-search`
- Denmark-specific and opt-in: `jobbank-search`, `jobdanmark-search`,
  `jobindex-search`, `jobnet-search`
- Any portal installed later through `/add-portal`

Honor each skill's `enabled` frontmatter. Do not enable a portal just because it is listed
here. For a CLI search, pass every configured target role family and applicable location
using that CLI's supported parameters; never invent flags or unsupported location codes.

## India boards (use when India is an explicit target market)

For an India search, use WebSearch with the following site-scoped templates for every
configured role family and target location. Group 3-8 related titles in one query when
possible, and include 1-3 high-signal skills. Do not add a location to a genuinely
remote-only search unless the role must be available to candidates in that location.

Define:
- `<ROLE_TERMS>`: the target job function and its explicit title synonyms
- `<SKILL_TERMS>`: 1-3 relevant skills from the profile
- `<LOCATION>`: each explicitly configured target city/region, or `India` for a
  country-wide preference

| Platform | WebSearch query template | Coverage note |
|---|---|---|
| Naukri.com | `site:naukri.com "<ROLE_TERMS>" "<SKILL_TERMS>" "<LOCATION>"` | Major Indian job board; indexed results may omit requisition details. |
| LinkedIn India | `site:linkedin.com/jobs ("<ROLE_TERMS>") ("<SKILL_TERMS>") ("India" OR "<LOCATION>")` | Also use the LinkedIn CLI when enabled; obey its low-volume/personal-use guidance. |
| Instahyre | `site:instahyre.com "<ROLE_TERMS>" "<SKILL_TERMS>" "<LOCATION>"` | Search-engine discovery only unless a supported portal CLI is installed. |
| Cutshort | `site:cutshort.io "<ROLE_TERMS>" "<SKILL_TERMS>" "<LOCATION>"` | Search-engine discovery only unless a supported portal CLI is installed. |
| Hirist | `site:hirist.tech "<ROLE_TERMS>" "<SKILL_TERMS>" "<LOCATION>"` | Search-engine discovery only unless a supported portal CLI is installed. |
| Indeed India | `site:in.indeed.com "<ROLE_TERMS>" "<SKILL_TERMS>" "<LOCATION>"` | Aggregator; verify at employer source before application. |
| Foundit | `site:foundit.in "<ROLE_TERMS>" "<SKILL_TERMS>" "<LOCATION>"` | Search-engine discovery only unless a supported portal CLI is installed. |
| Shine | `site:shine.com "<ROLE_TERMS>" "<SKILL_TERMS>" "<LOCATION>"` | Search-engine discovery only unless a supported portal CLI is installed. |
| TimesJobs | `site:timesjobs.com "<ROLE_TERMS>" "<SKILL_TERMS>" "<LOCATION>"` | Search-engine discovery only unless a supported portal CLI is installed. |
| Glassdoor India | `site:glassdoor.co.in/job "<ROLE_TERMS>" "<SKILL_TERMS>" "<LOCATION>"` | May expose listings without full descriptions; do not infer missing details. |
| Wellfound | `site:wellfound.com "<ROLE_TERMS>" "<SKILL_TERMS>" ("India" OR "<LOCATION>")` | Startup roles; use only if India is a target market. |
| We Work Remotely | `site:weworkremotely.com "<ROLE_TERMS>" "<SKILL_TERMS>"` | Check eligibility/country restrictions on the posting; remote does not mean worldwide. |

### Direct employer career pages

Search up to 10 explicitly named target employers per run (all if fewer), for every
configured role family and target location. Prefer the employer's official career site
discovered independently; query:

```
site:<verified-careers-host> ("<ROLE_TERM_1>" OR "<ROLE_TERM_2>") "<SKILL_TERM>" "<LOCATION>"
"<COMPANY_NAME>" careers ("<ROLE_TERM_1>" OR "<ROLE_TERM_2>") ("India" OR "<LOCATION>")
```

Never infer the official careers host from a search result or posting body alone. Verify
the host from the employer's independently found official website before treating it as
the employer's source. If the profile has fewer than 8 named employers, search only the
named employers; do not invent a target-company list. If none are named, report that
direct-company searches were not configured and search the boards instead.

## International platforms

Search only countries or regions explicitly recorded as targets in the candidate profile
or supplied in the current request. Use the same role-family and skill terms, localized
where appropriate, and include the actual target country/city:

| Market / platform | WebSearch query template |
|---|---|
| Visa/sponsorship-oriented, global: Arbeitnow | `site:arbeitnow.com "<ROLE_TERMS>" "<SKILL_TERMS>" "<COUNTRY>"` |
| Relocation roles: Relocate.me | `site:relocate.me "<ROLE_TERMS>" "<SKILL_TERMS>" "<COUNTRY>"` |
| International roles: Jaabz | `site:jaabz.com "<ROLE_TERMS>" "<SKILL_TERMS>" "<COUNTRY>"` |
| Australia: Seek | `site:seek.com.au "<ROLE_TERMS>" "<SKILL_TERMS>" "<CITY_OR_COUNTRY>"` |
| Germany: StepStone | `site:stepstone.de "<ROLE_TERMS>" "<SKILL_TERMS>" "<CITY_OR_COUNTRY>"` |
| United Kingdom: Reed | `site:reed.co.uk "<ROLE_TERMS>" "<SKILL_TERMS>" "<CITY_OR_COUNTRY>"` |
| UAE / Gulf: Bayt | `site:bayt.com "<ROLE_TERMS>" "<SKILL_TERMS>" "<CITY_OR_COUNTRY>"` |

Add relevant country-specific job boards when the user has named another target country.
Do not claim visa sponsorship from the board name or search snippet; confirm it from the
posting. Don't search abroad merely because the role is remote.

## Role-family query construction

Build search families from the candidate's explicit target roles/functions, preferred
seniority, and proven skills:

- **Primary role families:** strongest target functions, with 3-8 realistic title
  synonyms per family.
- **Adjacent roles:** include only adjacent functions the user explicitly approved or
  `/setup` recommended and the user accepted.
- **Key skills:** choose 1-3 distinctive profile-backed terms per query. Do not put
  unsupported skills into searches.
- **Languages:** translate role terms for each professional language in the profile when
  relevant to the market. A job requiring an undeclared language is excluded by the
  Language Gate; a higher-than-declared level is flagged for review.
- **Salary:** never place personal salary expectations into public queries. Use them
  only to flag a mismatch when a posting states comparable compensation.

Search every configured role family at every configured target location on each
applicable platform. If no target location is configured, do not infer one; search only
platforms and roles that can be meaningfully searched without a location and report the
missing location constraint. Use a platform's native location or recency filter when documented.
Where it has no recency filter, filter returned results client-side when dates exist and
mark undated results as `date unknown`.

## Preferences and filters

Use the candidate's explicit preferences from `CLAUDE.md` and
`.claude/skills/job-application-assistant/01-candidate-profile.md`:

- Target roles / functions and seniority
- Target companies and company exclusions
- Target countries, cities, commute, and relocation preferences
- Remote, hybrid, onsite, travel, and employment-type preferences
- Professional language and proficiency levels
- Salary only for comparison against a posting's stated range

If a value is missing, keep it unknown; do not infer it from residence or work history.
Exclude only explicit hard deal-breakers. Surface soft preference mismatches as flags.

## Date and result handling

- Prefer roles posted within the last 14 days or with a future application deadline.
- If posting date is unknown, include only if otherwise relevant and flag `date unknown`.
- Do not infer open/live status from a search result. `/apply` must re-verify the
  employer/official ATS posting before scoring or drafting.
- Deduplicate across all sources by canonical URL and company/title before detail fetch.
- Cap each search call at approximately 20 results (or the CLI's nearest documented
  limit). Paginate only when needed to cover the configured role/location scope.
- Record per-source coverage as searched, no results, unavailable, failed, disabled,
  not applicable, or deferred. A successful empty result is `no results`, not failure.

## Focus and unattended runs

For an interactive `/scrape <focus>`, prioritize the named focus while retaining other
configured families unless the user explicitly asks for a narrow search.

For `/scrape --unattended` or `/scrape --scheduled`, run every configured role-family
and location combination across all applicable platforms and the named employers. Do not
ask questions. If profile setup is incomplete, search the known combinations and clearly
report which coverage was impossible instead of guessing.
