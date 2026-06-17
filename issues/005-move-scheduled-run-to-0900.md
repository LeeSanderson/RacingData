# Move the scheduled run to 09:00

## Parent PRD

`issues/prd-forecast-odds.md`

## What to build

Move the daily Azure DevOps scheduled run from 06:00 to 09:00 so the schedule is fixed ahead of the Phase 2 live-odds work. Phase 1 itself does not need the later slot (the forecast is present at 06:00), but moving once now avoids a second schedule change later.

Change the cron in `.azuredevops/scheduled-run.yml` from `0 6 * * *` to `0 9 * * *` and update the `displayName` accordingly. No code change is required: `run.ps1`'s step order (`updateresults → validate → todaysracecards → build_features → predict`) is unchanged, and predictions continue to work running ~3 hours later because UK/IRE racing starts well after 09:00.

See the PRD's "Scheduling & wiring" section and user stories 9, 10.

## Acceptance criteria

- [ ] `.azuredevops/scheduled-run.yml` cron is `0 9 * * *` with a matching `displayName` (e.g. "Daily 9AM run").
- [ ] `run.ps1` is unchanged (step order intact).
- [ ] No regression to the prediction step from the later run time (UK/IRE racing starts after 09:00).

## Blocked by

None - can start immediately.

## User stories addressed

Reference by number from the parent PRD:

- User story 9
- User story 10
