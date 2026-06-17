## Parent PRD

`issues/prd.md` — "Feature exposed via the shared optional-predictor list",
"No new within-race `Rel` companion required", "Race selection unchanged"
(Implementation Decisions).

## What to build

Expose `MarketProb` as an optional model predictor so the algorithm families pick it up
through their common feature-universe selection, with no per-algorithm wiring for the
classifiers.

- Add `MarketProb` to the shared `OPTIONAL_PREDICTORS` list in
  `race_analytics/algorithms/base.py`. The win-classifier family and the XGBoost family
  (`nan_tolerant_predictors = OPTIONAL_PREDICTORS`) then include it automatically via
  `_feature_universe` / `_select_features`.
- **Verify and wire the regressor path.** `RegressorAlgorithm._select_features` adds only
  `REQUIRED_PREDICTORS + nan_tolerant_predictors`, and `RidgeRegressionAlgorithm` sets no
  `nan_tolerant_predictors` (defaults to `[]`) — so without explicit work Ridge will not
  select `MarketProb`. Make the regressor family actually include `MarketProb`, protected
  by the uniform-prior imputation (no NaN reaches the estimator).
- Do **not** add a separate within-race `Rel` companion (`MarketProb` is already
  normalized within the race).
- Do **not** introduce any odds-presence race-selection gate — the predicted population
  stays exactly as today.

## Acceptance criteria

- [ ] `MarketProb` is present in `OPTIONAL_PREDICTORS`.
- [ ] A test confirms a win-classifier-family algorithm selects `MarketProb` into its
      fitted feature set when the column is present.
- [ ] A test confirms the regressor family (incl. Ridge) selects `MarketProb` and that no
      NaN reaches the estimator (uniform-prior imputation holds).
- [ ] Race selection / predicted population is byte-for-byte unchanged on a fixture fold
      (no odds-presence gate introduced).

## Blocked by

- Blocked by `issues/002-materialize-market-prob-serving-path.md`
- Blocked by `issues/003-materialize-market-prob-training-path.md`

## User stories addressed

- User story 1 (algorithms can learn from the market signal)
- User story 6 (`MarketProb` added to the shared optional-predictor list; both families
  pick it up)
- User story 10 (race selection left unchanged)
