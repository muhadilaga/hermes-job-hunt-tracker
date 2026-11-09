# job-hunt-tracker — a Hermes plugin

A job-hunt tracker for Hermes Agent. It logs every job application
(company, position, channel, location, status, date sent, follow-up
date, notes), refuses to log the same company + position twice, and
lists what is due for follow-up — the everyday workflow of a job hunter,
as tools Hermes can call in chat.

No network calls, no accounts, no secrets. The log is a human-readable
JSON file in the plugin data directory, so it survives plugin updates.

## Tools

| Tool | What it does |
| --- | --- |
| `job_log_application` | Log a sent application. Rejects exact `company \|\| position` duplicates. Follow-up date defaults to 7 days after the send date. |
| `job_list_applications` | List logged applications, newest first. Optional `status` / `channel` filters. |
| `job_check_duplicate` | Check whether a company + position was already logged. Call before applying. |
| `job_update_status` | Change the status of a logged application (Sent, In Progress, Rejected, Interview, Accepted). |
| `job_followups_due` | Applications whose follow-up date is due within N days (default 7) or overdue, earliest first. Rejected/accepted are excluded. |
| `job_application_stats` | Total logged, counts by status and by channel. |

Examples (as the agent would call them):

- `job_log_application` — company "PT Phincon", position "Bootcamp Software Engineer", channel "JobStreet", location "Jakarta"
- `job_check_duplicate` — company "PT Phincon", position "Bootcamp Software Engineer"
- `job_followups_due` — within_days 7
- `job_update_status` — company "PT Phincon", position "Bootcamp Software Engineer", new_status "Interview"

## Install (Windows)

Install from the Git repo (a local-path install is not supported, and
copying the folder into `~\.hermes\plugins` does not register the plugin):

```powershell
hermes plugins install https://github.com/muhadilaga/hermes-job-hunt-tracker.git --enable
hermes plugins validate $env:LOCALAPPDATA\hermes\plugins\job-hunt-tracker --install-deps
hermes plugins doctor job-hunt-tracker --ci
```

Confirm it is registered and enabled with
`hermes plugins list --plain --no-bundled` — it should show
`enabled git 0.1.0 job-hunt-tracker`. Full manual test script:
see `TESTING.md`.

Notes:

- Plugins are opt-in: `hermes plugins enable job-hunt-tracker` is
  required before the tools appear.
- The log lives at
  `%LOCALAPPDATA%\hermes\plugin-data\job-hunt-tracker\applications.json`.
  It is plain JSON — you can read or back it up by hand. Never edit it
  while Hermes is running.
- Stdlib only, Python 3.14 compatible, zero third-party dependencies.

## Catalog submission (for the hackathon entry)

This plugin ships as a standalone repository. To get it into the Hermes
plugin catalog:

1. Push this folder to its own public GitHub repo.
2. Open a pull request against the Hermes agent repository adding one
   file, `plugin-catalog/job-hunt-tracker.yaml`, describing the plugin
   and pinning the exact reviewed commit (a full 40-character SHA —
   not a branch or a tag). A maintainer reviews and merges the entry.
3. Catalog CI runs `hermes plugins validate` against the pinned commit,
   so validate locally first (see Install above).

The entry is the PR itself; the demo video and the submission form are
separate steps of the hackathon and are not part of this repo.
