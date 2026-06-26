# Add `Kelly £` / `Kelly%` to the Early-vs-Late stability split

## Parent PRD

`issues/prd.md` — "Kelly-staked ROI in the evaluation metrics"

## What to build

Extend the Early-vs-Late stability split in `race_analytics/scripts/evaluate.py`
(`_print_early_late_split`) so each Early / Late period reports Kelly net £ and Kelly
coverage % alongside the existing accuracy / ROI / races / coverage columns — letting the
stability of an algorithm's *staked* edge be judged over time, not just its flat ROI.

The split currently works from the rank-1 picks (`all_preds`) and results
(`all_results_store`). For Kelly it needs the per-(algorithm, fold) full-field frames
retained in issue 002, split into the same early/late halves (recall the fold lists are
most-recent-first: the first half is Late, the second half is Early) and summarised once
per half with the shared `betting` function. Same locked metric and net-£ convention; no
diagnostic label.

## Acceptance criteria

- [ ] The Early-vs-Late table gains Kelly net £ and Kelly coverage % columns for each of the Early and Late periods
- [ ] Each period's Kelly figure is an additive summarise over that period's concatenated full-field frames (consistent with the early/late split used for the existing columns)
- [ ] A non-probabilistic algorithm shows `n/a` / 0% in both periods
- [ ] The existing accuracy / ROI / races / coverage columns in the split are unchanged
- [ ] pytest covers the early/late Kelly split on an eval-results-shaped fixture; `pytest tests/` passes

## Blocked by

- Blocked by `issues/002-evaluator-kelly-summary-table.md`

## User stories addressed

Reference by number from the parent PRD:

- User story 5 (Kelly net £ and coverage % in the Early-vs-Late stability split)
