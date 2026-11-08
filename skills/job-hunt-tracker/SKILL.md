---
name: job-hunt-tracker
description: Track job applications — log each application, check for duplicates before applying, and list follow-ups due. Use when the user talks about a job application, asks whether they already applied somewhere, or wants to know what to follow up on.
---

# Job Hunt Tracker

A small log for a job hunt, kept inside Hermes. Every application is one
record: company, position, channel, location, status, date sent,
follow-up date, and notes. The log lives in the plugin data directory as
human-readable JSON, so it survives plugin updates.

## When to use it

- The user says an application was sent, or asks to record one → `log_application`.
- The user asks about a new lead, or whether they already applied → `check_duplicate` first, before anything is logged or sent.
- The user asks what they applied to, or wants a review → `list_applications`.
- A reply arrives (interview invite, rejection, offer) → `update_status`.
- The user asks what to follow up on → `followups_due`.
- The user asks for an overview of the hunt → `application_stats`.

## The workflow

1. **Dedupe first.** Before logging or sending, call `check_duplicate`
   with the company and position. Matching is case-insensitive on
   `company || position`. If it returns `duplicate: true`, stop and tell
   the user — never apply twice to the same role.
2. **Log what was sent.** Call `log_application` with the facts only:
   company, position, channel (LinkedIn, Glints, JobStreet, Email,
   Indeed, Dealls, Company Website, ...), location, and date sent.
   The follow-up date defaults to 7 days after the send date.
3. **Follow up.** `followups_due` lists what is due within the next
   7 days or already overdue, earliest first. Rejected and accepted
   applications are excluded automatically.
4. **Keep statuses honest.** Update with `update_status` when something
   changes. Valid statuses: Terkirim, Dalam Proses, Ditolak, Interview,
   Diterima.

## Honesty rules — never break these

- Record only what the user states. Never invent or embellish a GPA,
  years of professional experience, English level, or skills.
- A fresh graduate has 0 years of professional experience; projects and
  freelance bids are not employment. Do not reword them into experience.
- If a fact is missing (salary, deadline, location), leave it out — do
  not fill it in with a guess.
- The plugin stores facts. It does not write cover letters and does not
  submit applications on its own.
