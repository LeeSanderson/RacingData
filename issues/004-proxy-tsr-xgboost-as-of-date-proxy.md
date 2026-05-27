# Issue 004: `ProxyTSRXGBoost` drops raw ratings and uses an as-of-date proxy

## Parent PRD

`issues/prd.md`

## What to build

Remove both leaks from `ProxyTSRXGBoostAlgorithm` (and inherited
`TunedProxyTSRXGBoostAlgorithm`): the primary leak (raw current-race RPR/TSR fed
as features) and the temporal leak (whole-window proxy aggregate that lets a
training row see the horse's future races). See the PRD's "`ProxyTSRModel` and
`ProxyTSRXGBoostAlgorithm`" implementation decision.

In `race_analytics/algorithms/proxy_tsr.py`:

- The `ProxyTSRModel` regressor stays fitted only on rows with a real
  `TopSpeedRating` — during evaluation this is the fold's training data, so no
  fold-day labels leak into the regressor (already the case; preserve it).
- Replace the whole-window `PeakProxyTSR/LastProxyTSR/Best5ProxyTSR` per-horse
  aggregate with an as-of-date "last prior proxy" per horse: the proxy value used
  for a given race must depend only on that horse's races *before* that race. The
  most-recent completed race's proxy is what serving uses for "today".

In `race_analytics/algorithms/proxy_tsr_xgboost.py`:

- Drop the raw current-race `RacingPostRating`/`TopSpeedRating` from the feature
  set. Use the same previous-race `LastRace*` rating features as
  `RatingsXGBoostAlgorithm` (issue 003) plus the as-of-date proxy feature(s).
- `TunedProxyTSRXGBoostAlgorithm` inherits the corrected behaviour unchanged.

The algorithm stays in the `ALGORITHMS` registry with no TSR gate (its purpose is
to predict horses lacking a real TSR via the proxy).

## Acceptance criteria

- [ ] The proxy value for a training row depends only on that horse's prior
      races: a test in `tests/algorithms/test_proxy_tsr.py` shows that adding a
      later (future) race for a horse does not change the proxy for an earlier row
- [ ] After `fit()`, the `ProxyTSRXGBoostAlgorithm` feature set contains **no**
      raw `RacingPostRating`/`TopSpeedRating` column and uses the `LastRace*`
      rating features plus the as-of-date proxy feature(s)
- [ ] `tests/algorithms/test_proxy_tsr_xgboost.py` is extended to assert the
      corrected feature set; the existing `predict` tests still pass
- [ ] `python -m race_analytics.scripts.evaluate --folds 2 --training-months 2
      --algorithms ProxyTSRXGBoostAlgorithm,TunedProxyTSRXGBoostAlgorithm` runs
      end-to-end without erroring

## Blocked by

- Blocked by `issues/002-horse-stats-carries-previous-race-ratings.md`

(May proceed in parallel with `issues/003-ratings-xgboost-previous-race-ratings.md`;
mirror its previous-race rating handling.)

## User stories addressed

Reference by number from the parent PRD:

- User story 11
- User story 12
- User story 13
- User story 14
- User story 21 (behaviour tests for this slice)
