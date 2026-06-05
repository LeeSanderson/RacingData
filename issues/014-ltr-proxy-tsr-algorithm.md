## Parent PRD

`issues/prd.md`

## What to build

Add a learning-to-rank algorithm in a new file `race_analytics/algorithms/ltr_proxy_tsr.py`. `LTRProxyTSRAlgorithm` inherits from `BinaryWinClassifierAlgorithm` but replaces the XGBoost binary classifier with `XGBRanker`.

Key implementation points:

- `fit()`: sort training data by `RaceId`, compute group sizes (horses per race), set labels = `HorseCount − FinishingPosition + 1` (winner gets highest label). Call `_ranker.fit(X, labels, group=group_sizes)`.
- `_run_prediction()`: call `_ranker.predict(X)` (returns scores). Store as `WinProbability` for interface compatibility (this is a ranking score, not a calibrated probability). Rank within race by score descending.
- Confidence gate: `AbstainWrapperLTRAlgorithm` sets `metric="gap"` (score gap between 1st- and 2nd-ranked horse), since `top_prob` is not meaningful for ranking scores.
- Register `LTRProxyTSRAlgorithm` and `AbstainWrapperLTRAlgorithm` in `__init__.py` `ALGORITHMS` list.

See PRD §LTRProxyTSRAlgorithm for full spec. Note the `WinProbability` naming caveat in PRD §Further Notes.

## Acceptance criteria

- [ ] `ltr_proxy_tsr.py` exists containing `LTRProxyTSRAlgorithm` and `AbstainWrapperLTRAlgorithm`.
- [ ] `AbstainWrapperLTRAlgorithm` uses `metric="gap"`.
- [ ] Both are present in the `ALGORITHMS` list in `__init__.py`.
- [ ] Smoke test in `tests/algorithms/test_ltr_proxy_tsr.py`: `fit()` + `predict_field()` completes without error on a small synthetic DataFrame and returns a result with `RaceId`, `HorseId`, `WinProbability`, and `PredictedRank` columns.
- [ ] `pytest` full suite passes.

## Blocked by

- Blocked by `issues/011-headgear-features.md`

## User stories addressed

- User story 7
- User story 8
- User story 12
