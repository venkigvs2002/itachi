# /schedule-nightly - Register the nightly job search on a cron schedule

Interactive setup wizard. Asks when the nightly run should fire, confirms where the report
goes, and registers the schedule. Run once; re-run to change it.

`$ARGUMENTS` may contain `--cancel` to remove an existing schedule (jump to the Cancel
section at the bottom) or `--list` to show what is registered.

---

## Step 0: Preflight — refuse to schedule a run that will fail

Run the same checks as `/nightly` Step 0 (placeholder grep on `CLAUDE.md`, master resume
`cv/main_example_improved.tex`, configured role and location in `search-queries.md`,
tracker header, `documents/README.md`).

**If any of them fail, do not schedule.** Show the failures and the fix (usually `/setup`),
then stop.

Scheduling a pipeline that aborts every night is worse than scheduling nothing. The user
gets a nightly "aborted at preflight" email, learns within a week to ignore the whole
thread, and then misses the first real failure. Make them fix the profile first.

---

## Step 1: Ask for the run time

Use `AskUserQuestion`. Offer:

| Option | Cron `M H` (local) |
|---|---|
| 11:28 PM | `28 23` |
| 11:03 PM | `3 23` |
| 12:07 AM | `7 0` |
| 2:00 AM | `0 2` |

Offer a custom time too, and convert whatever they give you.

**Nudge off `:00` and `:30`.** Every user who asks for "11:30" gets `30 23`, which means
scheduled jobs from across the fleet land on the same instant. The options above are
already nudged. Only use an exact `:00`/`:30` when the user explicitly insists on that
precise minute.

## Step 2: Ask for frequency

Use `AskUserQuestion`. Offer:

| Option | Cron day-of-week |
|---|---|
| Every night | `*` |
| Weekdays only | `1-5` |
| Weekly (Sunday night) | `0` |

"Every other day" is **not** expressible in a 5-field cron day-of-week. If the user wants
it, say so plainly and offer weekdays-only as the nearest equivalent rather than silently
registering something different.

## Step 3: Confirm the report destination

Show the email address you believe is the user's and ask them to confirm or correct it.
**Ask — do not read it from session context and assume.** The account identity can change
between sessions, and a nightly report quietly going to a stale address is a failure that
looks like success.

Also offer "no email, file only," which maps to `/nightly --no-email`.

---

## Step 4: Build the cron expression — local time, no UTC conversion

Assemble `M H * * DoW` from Steps 1 and 2 **in the machine's local timezone**.

> **Do not convert to UTC.** `CronCreate` takes cron in the user's local timezone —
> `0 9 * * *` means 9am local. This machine is on IST (+05:30). An earlier version of this
> spec carried a UTC conversion table (`11:30 PM IST → 0 18 * * *`); applying it here would
> fire the job at **6:00 PM IST**, five and a half hours early. 11:30 PM IST is `30 23 * * *`.
> If you are editing this file and feel the urge to add a timezone conversion, that is the
> bug, not the fix.

Show the user the assembled expression and what it means in plain words before registering.

---

## Step 5: Register with CronCreate

Call `CronCreate` with `recurring: true`, the expression from Step 4, and a
**self-contained** prompt. Each firing starts a fresh session with no memory of this
conversation, so the prompt must carry everything it needs:

```
Scheduled nightly job search. This is an automated non-interactive run.

Working directory: <absolute path to this cloned workspace>

Run: /nightly --max-drafts 3 --email <confirmed address>

Rules for this run:
- Never prompt or ask a question. If you would normally ask, record it in the report and continue.
- Never open a browser, fill an application form, or submit an application.
- Never write the `prepped` tracker status.
- Do not invoke /status and do not scan Gmail for application responses.
- End by emailing the report and printing a one-line summary.
```

Substitute the real address. Keep `--max-drafts` at 3 unless the user asked otherwise.

---

## Step 6: Confirm — with the real caveats

Report the **actual next run time from the `CronCreate` result**, not the minute in the
cron expression; the scheduler applies a per-job offset.

Then state these plainly. Do not paper over them:

- **The schedule lives only in this Claude Code session.** It is held in memory, nothing
  is written to disk, and it is gone when you close Claude Code. Leaving the terminal open
  overnight is what makes a "nightly" run actually nightly.
- **It fires only while the session is idle** — not while another query is mid-flight.
- **Recurring jobs auto-expire after 7 days.** It fires one last time, then deletes
  itself. Re-run `/schedule-nightly` weekly, or move to the durable option below.
- **The durable alternative is a cloud routine** via the `/schedule` skill, which runs
  server-side and survives reboots. It is not wired up yet: it requires this workspace
  committed and pushed to a remote the cloud runner can access, plus confirmation that
  the cloud sandbox has `lualatex` and `bun` for CV compilation and the portal CLIs. Say
  this is available on request rather than implying it already works.

Do **not** print a flat "your nightly job search is live, you'll wake up to a report"
confirmation. For a session-only job that overpromises. Something like:

> Registered: nightly search at 11:28 PM IST, weekdays, report to <address>.
> Next run: <actual next-run time from the tool result>.
> Keep this Claude Code session open — the schedule is in-memory and expires in 7 days.

---

## Cancel (`--cancel`)

1. `CronList` to find the registered job.
2. If there is no nightly job, say so and stop — do not delete an unrelated job.
3. `CronDelete` with its ID.
4. Confirm it is gone with a second `CronList`.

## List (`--list`)

`CronList` and show each job's expression and next run time. If none, say the nightly
search is not currently scheduled.
