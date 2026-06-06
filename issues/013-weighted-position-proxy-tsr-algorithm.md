## Parent PRD

`issues/prd.md`

## What to build

Add `WeightedPositionProxyTSRAlgorithm` to `race_analytics/algorithms/proxy_tsr_xgboost.py`. This variant overrides `fit()` to weight training samples by `1 / FinishingPosition` (winner = 1.0, 2nd = 0.5, …), passing `sample_weight` to `_classifier.fit()`. Everything else is inherited from `ProxyTSRXGBoostAlgorithm`.

Also add `AbstainWeightedPositionAlgorithm` (inherits `AbstainWrapperAlgorithm`, sets base to `WeightedPositionProxyTSRAlgorithm`) and register both in `race_analytics/algorithms/__init__.py` `ALGORITHMS` list.

See PRD §WeightedPositionProxyTSRAlgorithm for full spec.

## Acceptance criteria

- [ ] `WeightedPositionProxyTSRAlgorithm` exists in `proxy_tsr_xgboost.py` and passes `sample_weight = 1 / FinishingPosition` to `_classifier.fit()`.
- [ ] `AbstainWeightedPositionAlgorithm` exists and wraps `WeightedPositionProxyTSRAlgorithm`.
- [ ] Both are present in the `ALGORITHMS` list in `__init__.py`.
- [ ] `pytest` full suite passes (no dedicated unit test required per PRD — correctness verified via eval in `issues/017-evaluation-run-and-adoption.md`).

## Blocked by

- Blocked by `issues/011-headgear-features.md`

## User stories addressed

- User story 6
- User story 12
