## Parent PRD

`issues/prd.md`

## What to build

Add a second summary table printed after the existing accuracy/ROI summary, showing mean and standard deviation of fit and predict times per algorithm across all folds.

End-to-end behaviour: after the existing `=== Summary ===` table, a second table appears:
```
=== Timing Summary ===
Algorithm                                 Fit(avg)   Fit(std)  Pred(avg)  Pred(std)
--------------------------------------------------------------------------------------
  XGBoostAlgorithm                          1.234      0.012      0.056      0.003
```

See the Timing summary table section of the parent PRD.

## Acceptance criteria

- [ ] A `=== Timing Summary ===` table is printed after the existing accuracy/ROI summary
- [ ] Columns are: `Algorithm`, `Fit(avg)`, `Fit(std)`, `Pred(avg)`, `Pred(std)`, all in seconds to 3 decimal places
- [ ] Values are computed from the `all_fit_times` / `all_predict_times` accumulators introduced in `issues/001-timing-capture-per-fold-display.md`
- [ ] A pure helper function (e.g. `_aggregate_times`) encapsulates mean/std computation and is tested in isolation
- [ ] Unit tests in `tests/scripts/test_evaluate.py` assert correct mean and std output for known input lists
- [ ] Algorithms with no completed folds show `N/A` in all timing columns, consistent with the accuracy table

## Blocked by

- `issues/001-timing-capture-per-fold-display.md`

## User stories addressed

- User story 4
- User story 5
- User story 18 (partially — `_aggregate_times` extracted as a testable pure function)
