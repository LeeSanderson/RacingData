## Parent PRD

`issues/prd.md`

## What to build

A new `ProxyTSRXGBoostAlgorithm` class that uses `ProxyTSRModel` internally to extend the `RatingsXGBoostAlgorithm` approach to all races — without any TSR gating. Register it in the algorithm registry so it appears automatically in `evaluate.py` output alongside existing algorithms.

The class must:
- Implement the standard `fit(train_df)` / `predict(races, horse_stats, jockey_stats)` interface from `BaseAlgorithm`.
- In `fit`: instantiate and fit a `ProxyTSRModel`, call `compute_horse_proxy_tsr(train_df)` and store the result as internal state, merge proxy TSR aggregates into the training data, compute relative proxy TSR features (`RelPeakProxyTSR`, `RelLastProxyTSR`, `RelBest5ProxyTSR`) by extending the `_add_race_context` pattern (horse value minus race-card mean), then train an `XGBClassifier` on the full feature set: existing `PREDICTORS` + real TSR features (with NaNs where absent) + 6 proxy TSR features (3 absolute + 3 relative).
- In `predict`: merge stored proxy TSR aggregates onto the race card, compute relative proxy TSR features, then predict on **all** races that pass the standard `KnownHorseAndJockey` and `max_horses` filters — no `require_tsr` gate.
- Be registered in `race_analytics/algorithms/__init__.py` so that running `evaluate.py` without `--algorithms` includes it in the comparison table.

Existing algorithms (`RatingsXGBoostAlgorithm`, `RatingsXGBoostUngatedAlgorithm`, `RidgeRegressionAlgorithm`, `XGBoostAlgorithm`) must remain completely unchanged.

See the Implementation Decisions section of the PRD for full details on feature columns, relative feature computation, and XGBClassifier hyperparameters.

## Acceptance criteria

- [ ] `ProxyTSRXGBoostAlgorithm` appears in the `evaluate.py` summary table when run without `--algorithms`.
- [ ] The algorithm predicts on races that contain horses with no real `TopSpeedRating` (no TSR gating applied).
- [ ] The algorithm predicts on more races per fold than `RatingsXGBoostAlgorithm` (TSR-gated), targeting the full `KnownHorseAndJockey` race population.
- [ ] Feature set includes both real `TopSpeedRating` (NaN-tolerant) and the six proxy TSR columns.
- [ ] Relative proxy TSR features (`RelPeakProxyTSR`, etc.) are computed per race card, matching the pattern used for `RelTopSpeedRating`.
- [ ] Existing algorithm evaluation results are unaffected (same accuracy/ROI as before this change).
- [ ] Unit tests in `tests/algorithms/test_proxy_tsr_xgboost.py` verify: fit completes on synthetic data, predict returns a DataFrame with `RaceId`/`HorseId` columns with one row per race, and races with no real TSR are not filtered out.

## Blocked by

- `issues/001-proxy-tsr-model.md`

## User stories addressed

- User story 1 — predictions on more than 1–2 races per day
- User story 2 — predictions on races containing lightly-raced or debutant horses
- User story 5 — proxy rating reflects peak, last, and best-of-5 form
- User story 6 — independently evaluated against existing algorithms
- User story 9 — registered in evaluation registry for automatic comparison
- User story 10 — walk-forward correctness maintained (proxy model trained only on data before fold date)
- User story 11 — real `TopSpeedRating` retained alongside proxy TSR features
- User story 12 — relative proxy TSR features computed per race card
- User story 14 — existing algorithms left completely unchanged
