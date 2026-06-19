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

---

## Completed — 2026-06-19 (HITL, decided with Lee)

**Decisions (Lee):**
- **Trigger: coverage-gated, not a date.** Re-run the A/B once `ForecastDecimalOdds`
  coverage in the 7-month training window reaches **≥ 80%** real-forecast rows (SP fallback
  excluded). Chosen with the months-away reality in mind: forecast capture is forward-only
  (began ~2026-06), so an ≥80% window won't exist until ~Jan 2027; the ~mid-Jul 2026
  one-month checkpoint is ~6/7 SP and informational-only.
- **Mechanism: recorded in `issues/todo.md`, no cloud cron.** The backlog file is what
  agents read when the active `issues/` queue is empty, so the durable written trigger
  there *is* the reminder — appropriate for a data-condition trigger ~6–7 months out rather
  than relying on a cron firing reliably that far ahead.

**Done:**
- `issues/todo.md` → "Re-evaluate MarketProb on honest forecast-fed data" rewritten as the
  concrete coverage-gated reminder: ≥80% trigger, what to do when it fires (re-run A/B,
  reconsider `ACTIVE_ALGORITHM` against the ROI + early/late stability gate, not accuracy),
  and a link to the diagnostic baseline in `evaluations.md`.
- `evaluations.md` → added an "⏰ Re-eval trigger (issue 009)" note under the SP-placeholder
  diagnostic, recording the ≥80% threshold and pointing forward to the reminder.

**Acceptance criteria — all met:**
- [x] Coverage threshold agreed (≥80%), chosen against the months-away reality.
- [x] Reminder recorded (in `issues/todo.md`) pointing back at re-running the A/B on
      forecast-fed data and reconsidering `ACTIVE_ALGORITHM` against the existing gate.
- [x] Threshold + link to the diagnostic in `evaluations.md` recorded so the reminder is
      actionable.
