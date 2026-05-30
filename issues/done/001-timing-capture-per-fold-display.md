## Parent PRD

`issues/prd.md`

## What to build

Instrument the walk-forward fold loop in `evaluate.py` to capture separate fit and predict times for each algorithm on each fold. Display times appended to the existing per-fold console line.

End-to-end behaviour: running `evaluate.py` produces lines like:
```
  XGBoostAlgorithm: accuracy=0.267, roi=15.123, races=121 | favourite: accuracy=0.156, roi=-10.567, races=121 | fit=1.234s, predict=0.056s
```

See the Timing capture and per-fold display sections of the parent PRD.

## Acceptance criteria

- [ ] `all_fit_times` and `all_predict_times` accumulators (dicts of `list[float]`) are populated with one entry per fold per algorithm, measured in seconds using `time.perf_counter()`
- [ ] Fit and predict times are measured independently — fit time covers only `algo.fit()`, predict time covers only `algo.predict()`
- [ ] Each per-fold console line ends with `| fit=X.XXXs, predict=X.XXXs` (seconds, 3 decimal places)
- [ ] The existing per-fold output (accuracy, roi, races, favourite metrics) is unchanged
- [ ] Unit tests in `tests/scripts/test_evaluate.py` assert that the accumulators are populated with the correct number of entries after a run with a minimal stub algorithm

## Blocked by

None — can start immediately.

## User stories addressed

- User story 1
- User story 2
- User story 3
