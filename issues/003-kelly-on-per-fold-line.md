# Add `Kelly £` / `Kelly%` to the per-fold line

## Parent PRD

`issues/prd.md` — "Kelly-staked ROI in the evaluation metrics"

## What to build

Extend the per-fold output in `race_analytics/scripts/evaluate.py` so each fold's printed
line reports that fold's Kelly net £ and Kelly coverage % alongside the accuracy / ROI /
favourite figures already printed, letting the staked return be watched accumulating fold
by fold.

This reuses the shared `betting` summariser and the per-fold full-field frames retained in
issue 002 — here scoped to the single fold rather than the cross-fold concatenation. As the
PRD's Placement bullet notes, the per-fold print must be **reordered** so the fold's
staking frame is built before the line is printed (today the line is printed inside the
algorithm loop before `_build_csv_rows` runs). Same locked metric and net-£ convention as
the Summary table; no diagnostic label.

## Acceptance criteria

- [ ] Each fold's per-algorithm output line includes the fold's Kelly net £ and Kelly coverage %
- [ ] The fold's staking frame is built before the per-fold line is printed (print reordered accordingly)
- [ ] A non-probabilistic algorithm shows `n/a` / 0% on the per-fold line
- [ ] The accuracy / ROI / favourite figures already on the per-fold line are unchanged
- [ ] pytest covers the per-fold Kelly figure on an eval-results-shaped fixture; `pytest tests/` passes

## Blocked by

- Blocked by `issues/002-evaluator-kelly-summary-table.md`

## User stories addressed

Reference by number from the parent PRD:

- User story 4 (Kelly net £ and coverage % on the per-fold line)
