## Parent PRD

`issues/prd.md` — "Adoption is gated on honest data, not this run" (Implementation
Decisions); "Choosing the exact re-eval date or coverage threshold" (Out of Scope —
the PRD commits to scheduling a reminder, not a specific date).

## What to build

Schedule a reminder to re-run the evaluation and reconsider adoption once
`ForecastDecimalOdds` coverage in history is meaningful — at which point the diagnostic
numbers from `issues/007` are replaced by an honest, forecast-fed read and adoption is
weighed against the normal gate (ROI and early/late stability).

**HITL** because the PRD deliberately does not fix the date or coverage threshold: you
choose the trigger (a coverage threshold and/or a date), informed by the "a fully
forecast-fed window is months away / a ~1-month checkpoint is still ~6/7 SP" reasoning in
the PRD's Further Notes.

## Acceptance criteria

- [ ] A coverage threshold and/or date for the re-eval is agreed (not hard-coded blindly —
      chosen with the months-away reality in mind).
- [ ] A reminder is scheduled (e.g. via `/schedule`) that, when it fires, points back at
      re-running the A/B on forecast-fed data and reconsidering `ACTIVE_ALGORITHM` against
      the existing gate.
- [ ] The chosen threshold/date and the link to the diagnostic in `evaluations.md` are
      recorded so the reminder is actionable, not forgotten.

## Blocked by

- Blocked by `issues/007-diagnostic-ab-rerun-record.md`

## User stories addressed

- User story 17 (reminder scheduled to re-evaluate once forecast coverage is meaningful)
- User story 20 (re-eval threshold chosen against the months-away reality, not a hard date)
