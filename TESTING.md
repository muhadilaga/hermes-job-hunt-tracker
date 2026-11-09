# Manual testing — job-hunt-tracker

Run these on the Windows PC where Hermes is installed. All commands are
PowerShell, run from the folder that contains `hermes-job-hunt-tracker`.

## 1. Install

Install from the Git repo (a local-path install is not supported, and
copying the folder into `~\.hermes\plugins` does not register the plugin):

```powershell
hermes plugins install https://github.com/muhadilaga/hermes-job-hunt-tracker.git --enable
```

Expected: the plugin lands in
`%LOCALAPPDATA%\hermes\plugins\job-hunt-tracker` and is enabled.

## 2. Validate (the same check catalog CI runs)

```powershell
hermes plugins validate $env:LOCALAPPDATA\hermes\plugins\job-hunt-tracker --install-deps
```

Expected: validation passes with no errors. The "declared tools" check
compares `plugin.yaml` against what `register()` registers — all six
tools must match.

## 3. Doctor (loads the plugin in isolation, temp HERMES_HOME)

```powershell
hermes plugins doctor job-hunt-tracker --ci
```

Expected: exit code 0. If doctor reports a failure, it prints the
traceback — fix that line and re-run.

## 4. Enable and confirm it loads

```powershell
hermes plugins enable job-hunt-tracker
hermes plugins list
```

Expected: the list shows `job-hunt-tracker`. Confirm it is registered
and enabled:

```powershell
hermes plugins list --plain --no-bundled
```

Expected: a line `enabled git 0.1.0 job-hunt-tracker`. (There is no
`/plugins` chat command in Hermes v0.23.0.)

If the plugin does not appear, run with discovery logging:

```powershell
$env:HERMES_PLUGINS_DEBUG=1; hermes plugins list
```

## 5. Try the tools in Hermes chat

Ask Hermes these, in order. Each line shows what should happen.

If the agent answers with raw Python instead of calling a tool, ask it
explicitly, e.g. "Panggil tool job_log_application dari plugin
job-hunt-tracker ...". The tools are exposed to the agent, but it does
not always pick them unprompted.

### a. Log one application

> Catat lamaran ke PT Phincon, Bootcamp Software Engineer, via JobStreet, Jakarta.

Expected: Hermes calls `job_log_application` and replies that it was logged,
with status Sent, today's date, and a follow-up date 7 days out.
The store file
`%LOCALAPPDATA%\hermes\plugin-data\job-hunt-tracker\applications.json`
now contains one entry.

### b. Check the duplicate

> Udah pernah lamar ke PT Phincon buat Bootcamp Software Engineer belum?

Expected: Hermes calls `job_check_duplicate` and answers that it was already
logged (with the send date). Try logging the same application again —
`job_log_application` must refuse with an "Already logged" error, not a
second entry. (In practice the agent may call `job_check_duplicate` first
and refuse to call `job_log_application` at all. Either way the assertion
is the same: no second entry is created.)

### c. List follow-ups due

> Lamaran apa yang harus di-follow up minggu ini?

Expected: Hermes calls `job_followups_due` and lists the Phincon entry
(follow-up date within 7 days).

### d. Update the status

> Ubah status lamaran Phincon jadi Interview.

Expected: Hermes calls `job_update_status` and confirms the change from
Sent to Interview. `job_followups_due` afterwards still lists it
(Interview is not a terminal status).

## 6. Failure cases worth checking

- Log an application with no company → clear "company is required" error.
- `job_update_status` for a company never logged → "Not found" error telling
  the user to log it first.
- `job_followups_due` with `within_days` 0 → only overdue and due-today items.
