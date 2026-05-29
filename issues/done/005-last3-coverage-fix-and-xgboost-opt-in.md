# Issue 005 — Move `Last3*` into the NaN-tolerant tier + XGBoost-family opt-in + lock-in test

## Parent PRD

`issues/prd.md` — Phase B.

## What to build

The behaviour-changing slice. Phase A already built the machinery
(`REQUIRED_PREDICTORS` / `OPTIONAL_PREDICTORS`, `nan_tolerant_predictors`,
`BinaryWinClassifierAlgorithm`'s two-tier dropna). This slice flips the switch
so XGBoost-family algorithms keep races where some horses have NaN `Last3*`
columns, while Ridge stays NaN-intolerant by construction.

- Confirm `OPTIONAL_PREDICTORS` in `race_analytics/algorithms/base.py` contains
  `["Last3RaceAvgSpeed", "Last3RaceSpeedTrend", "Last3AvgRelFinishingPosition"]`
  (already set in issue 002). No change to `REQUIRED_PREDICTORS` —
  `Trainer*` columns explicitly stay required per the PRD's Out-of-Scope.
- Set `nan_tolerant_predictors = OPTIONAL_PREDICTORS` on:
  - `XGBoostAlgorithm`
  - `RatingsXGBoostAlgorithm` (inherited automatically by
    `RatingsXGBoostUngatedAlgorithm`)
  - `ProxyTSRXGBoostAlgorithm` (inherited automatically by
    `TunedProxyTSRXGBoostAlgorithm`)
- `RidgeRegressionAlgorithm` keeps the default empty list. Its sklearn
  pipeline (`StandardScaler → PolynomialFeatures → Ridge`) cannot tolerate
  NaN, so the `Last3*` columns are effectively dropped from Ridge's feature
  list when rows containing them get filtered out. This is the intended
  behaviour per user story 11.

### Lock-in test

Add a focused unit test (e.g. `tests/race_analytics/algorithms/test_last3_nan_tolerance.py`)
that constructs synthetic training and race-card frames where:

- Some horses have NaN in one or more `Last3*` columns.
- All other `REQUIRED_PREDICTORS` columns are non-null.

Assertions:

- `XGBoostAlgorithm.fit(train_df)` succeeds and the post-dropna row count
  equals the input row count (no rows lost to `Last3*` NaN).
- `XGBoostAlgorithm.predict(...)` produces a non-empty frame for races
  whose horses include some `Last3*` NaN values.
- The same holds for `RatingsXGBoostAlgorithm` (ungate it for the test or
  test `RatingsXGBoostUngatedAlgorithm`) and `ProxyTSRXGBoostAlgorithm`.
- `RidgeRegressionAlgorithm.fit(train_df)` drops the rows with NaN `Last3*`
  columns from its training data (confirmed via fitted predictor count or
  by asserting a row with NaN `Last3*` does not appear in `_fitted_predictors`
  coverage).

## Acceptance criteria

- [ ] `nan_tolerant_predictors = OPTIONAL_PREDICTORS` set on
      `XGBoostAlgorithm`, `RatingsXGBoostAlgorithm`, and
      `ProxyTSRXGBoostAlgorithm`.
- [ ] `RidgeRegressionAlgorithm.nan_tolerant_predictors` stays empty.
- [ ] New unit test under `tests/race_analytics/algorithms/` covers the
      four assertions above and is green.
- [ ] Every existing test under `tests/race_analytics/algorithms/` still
      passes.
- [ ] `ALGORITHMS` / `ACTIVE_ALGORITHM` shape unchanged.

## Blocked by

- Blocked by `issues/002-nan-tolerant-predictors-two-tier-dropna.md`.
- Blocked by `issues/004-migrate-classifiers-and-smoke-eval.md`.

## User stories addressed

- User story 1
- User story 7
- User story 11
- User story 16
