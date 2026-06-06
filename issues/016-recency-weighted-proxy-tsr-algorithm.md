## Parent PRD

`issues/prd.md`

## What to build

Add `RecencyWeightedProxyTSRAlgorithm` to `race_analytics/algorithms/proxy_tsr_xgboost.py`. This variant overrides `fit()` to apply exponential decay weights to training samples so that recent races are weighted more heavily than stale form from 6–7 months ago.

Key implementation points:

- Constructor accepts `decay_lambda: float = 0.01` (half-weight at ~70 days).
- `fit()` override: infer the fold date as `train_df["Off"].max().date() + timedelta(days=1)`. Compute `days_ago = fold_date − race_date` for each training row. Set `sample_weight = exp(−decay_lambda × days_ago)`. Pass to `_classifier.fit()`.
- `AbstainRecencyWeightedAlgorithm` wraps `RecencyWeightedProxyTSRAlgorithm`.
- Register both in `__init__.py` `ALGORITHMS` list.

See PRD §RecencyWeightedProxyTSRAlgorithm for full spec.

## Acceptance criteria

- [ ] `RecencyWeightedProxyTSRAlgorithm` exists in `proxy_tsr_xgboost.py` and passes exponentially decayed `sample_weight` to `_classifier.fit()`.
- [ ] `AbstainRecencyWeightedAlgorithm` exists and wraps `RecencyWeightedProxyTSRAlgorithm`.
- [ ] Both are present in the `ALGORITHMS` list in `__init__.py`.
- [ ] `pytest` full suite passes (no dedicated unit test required per PRD — correctness verified via eval in `issues/017-evaluation-run-and-adoption.md`).

## Blocked by

- Blocked by `issues/011-headgear-features.md`

## User stories addressed

- User story 11
- User story 12
