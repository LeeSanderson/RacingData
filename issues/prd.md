# PRD: Proxy TopSpeed Rating for Broader Race Prediction Coverage

## Problem Statement

The current best-performing algorithm (`RatingsXGBoostAlgorithm` with TSR gating) achieves 0.602 accuracy and +313 ROI across a 60-fold backtest, but only by restricting predictions to races where **every horse has a Racing Post `TopSpeedRating` (TSR)**. This filter passes only ~1.6 races per day (10% of available races). On the remaining 90% of race days — where TSR is absent for at least one runner — the ungated algorithm falls back to 0.304 accuracy and a much lower ROI per race (+0.27 vs +3.37).

`TopSpeedRating` is a proprietary Racing Post metric that requires extensive race history per horse. It is unavailable for new or lightly-raced horses, which is why whole race days can have 0% TSR coverage. There is no way to obtain it for those horses.

The punter therefore faces a painful tradeoff: accept very low betting volume (1–2 races/day) or accept much weaker predictions. A proxy speed rating that approximates TSR from available race data would unlock broader coverage without sacrificing prediction quality.

## Solution

Train an XGBoost regression model (`ProxyTSRModel`) to predict what Racing Post's `TopSpeedRating` would be for any horse-race combination, using only data that is always available: raw race time, distance, surface, going, race type, course, weight, finishing position, beaten distance, and field size. The 49% of historical rows that carry a real `TopSpeedRating` serve as labelled training examples.

For each horse, aggregate the per-race proxy predictions into three summary statistics (all-time peak, most recent, and best of last 5 races). Use these as additional features — alongside the real `TopSpeedRating` where it exists — in a new algorithm class (`ProxyTSRXGBoostAlgorithm`) that predicts on **all** races without any TSR gate. Compare this algorithm against all existing algorithms in the walk-forward evaluation to determine whether proxy TSR provides genuine lift on the full race population.

## User Stories

1. As a punter, I want predictions on more than 1–2 races per day, so that I have a meaningful number of betting opportunities each day.
2. As a punter, I want predictions on races containing lightly-raced or debutant horses, so that I am not systematically excluded from those markets.
3. As a punter, I want the algorithm to use a horse's computed speed history even when Racing Post has not published a TSR, so that the absence of a proprietary rating does not make the prediction blind.
4. As a punter, I want the proxy speed rating to normalise for race conditions (surface, going, distance, course), so that a horse's figure is comparable across different race types and tracks.
5. As a punter, I want the proxy rating to reflect a horse's best recent form (peak, last run, best of last 5), so that the algorithm distinguishes a horse returning to form from one in decline.
6. As a punter, I want the new algorithm to be independently evaluated against existing algorithms, so that I can make an informed choice about which to follow.
7. As a developer, I want the proxy TSR computation encapsulated in a standalone `ProxyTSRModel` class, so that it can be reused, tested in isolation, and potentially moved to a preprocessing step later.
8. As a developer, I want `ProxyTSRModel` to have a configurable `min_races` threshold (default 1), so that I can tune how much race history is required before a proxy rating is trusted.
9. As a developer, I want the new `ProxyTSRXGBoostAlgorithm` registered in the evaluation registry alongside the existing algorithms, so that a single `evaluate.py` run produces a fair comparison across all approaches.
10. As a developer, I want walk-forward correctness maintained, so that the proxy TSR model is only ever trained on data before the fold date and never leaks future information.
11. As a developer, I want real `TopSpeedRating` retained in the new algorithm's feature set alongside proxy TSR features, so that the classifier can learn to weight the authoritative signal appropriately when it is available.
12. As a developer, I want relative proxy TSR features (horse's proxy TSR minus the race-card mean) computed in addition to absolute values, so that the classifier sees each horse's speed figure in the context of its field — consistent with how real `RelTopSpeedRating` is already used.
13. As a developer, I want the `ProxyTSRModel` to be label-encode `CourseName` with a safe fallback for unseen courses, so that prediction never fails for a track not seen during training.
14. As a developer, I want existing algorithms (`RatingsXGBoostAlgorithm`, `RatingsXGBoostUngatedAlgorithm`, `RidgeRegressionAlgorithm`, `XGBoostAlgorithm`) left completely unchanged, so that their evaluation baselines remain stable.

## Implementation Decisions

### New module: `ProxyTSRModel`

- Encapsulates an `XGBRegressor` trained to predict `TopSpeedRating` from per-race outcome data.
- **Constructor parameter**: `min_races: int = 1` — horses with fewer historical races than this threshold receive NaN proxy TSR values.
- **`fit(train_df)`**: trains the regressor using rows where `TopSpeedRating` is not NaN as labelled examples. Features: `Speed`, `DistanceInMeters`, `WeightInPounds`, `HorseCount`, surface/going/race-type one-hot columns (already encoded in `train_df`), `CourseName` (label-encoded integer), `FinishingPosition`, `OverallBeatenDistance`.
- **`compute_horse_proxy_tsr(train_df) -> DataFrame`**: applies the fitted regressor to every row in `train_df` (including rows without a real TSR), then aggregates per `HorseId` into three columns: `PeakProxyTSR` (all-time best), `LastProxyTSR` (most recent race), `Best5ProxyTSR` (best across last 5 races). Horses below the `min_races` threshold are set to NaN across all three. Returns a DataFrame keyed by `HorseId`.
- `CourseName` encoding: `sklearn.preprocessing.LabelEncoder` fit on training data; unseen courses at predict time mapped to a dedicated "unknown" integer (e.g. `-1`).
- Lives in a new file alongside the other algorithm modules.

### New module: `ProxyTSRXGBoostAlgorithm`

- Inherits the same `fit` / `predict` interface as existing algorithms (`BaseAlgorithm`).
- **`fit(train_df)`**:
  1. Instantiates and fits `ProxyTSRModel` on `train_df`.
  2. Calls `compute_horse_proxy_tsr(train_df)` and stores the result as internal state (`_horse_proxy_tsr`).
  3. Merges proxy TSR aggregates into `train_df` per `HorseId`.
  4. Calls `_add_race_context()` (extended to handle the three new proxy columns, computing their relative versions: `RelPeakProxyTSR`, `RelLastProxyTSR`, `RelBest5ProxyTSR`).
  5. Trains an `XGBClassifier` (same hyperparameters as `RatingsXGBoostAlgorithm`: 200 trees, lr=0.05, depth=4) on the full feature set: existing `PREDICTORS` + real TSR features (`TopSpeedRating`, `RacingPostRating`, `OfficialRating` + their relative forms) + 6 proxy TSR features (3 absolute + 3 relative).
- **`predict(race_card, horse_stats, jockey_stats)`**:
  1. Merges `_horse_proxy_tsr` onto race card horses (NaN for horses with no history).
  2. Computes relative proxy TSR features across the race card via `_add_race_context()`.
  3. **No TSR gating** — predicts on all races that pass the standard `KnownHorseAndJockey` and `max_horses` filters.
  4. Returns `(RaceId, HorseId)` pairs for predicted winners.
- Lives in a new file alongside the other algorithm modules.

### Changes to `_add_race_context()`

- Extend the relative-feature computation to also handle `PeakProxyTSR`, `LastProxyTSR`, `Best5ProxyTSR` — each producing a `Rel*` column by subtracting the race-card mean, mirroring the existing pattern for real ratings.

### Changes to algorithm registry (`__init__.py`)

- Import and register `ProxyTSRXGBoostAlgorithm` in the `ALGORITHMS` list so it appears automatically in `evaluate.py` runs.

### No changes to `evaluate.py`, `_engineer_features`, or `_race_card`

- The proxy TSR computation is entirely internal to the algorithm's `fit()`/`predict()` cycle — it requires no changes to the evaluation harness, preprocessing pipeline, or CSV schema.

## Testing Decisions

A good test for `ProxyTSRModel` exercises its external contract — `fit` then `compute_horse_proxy_tsr` — using a small synthetic DataFrame, and asserts on the shape and semantics of the output (correct columns, NaN for horses below `min_races`, non-NaN for horses with sufficient history, `Best5ProxyTSR ≤ PeakProxyTSR` by definition). Implementation details of the regressor should not be asserted.

A good test for `ProxyTSRXGBoostAlgorithm` calls `fit(train_df)` then `predict(card, horse_stats, jockey_stats)` on synthetic data and asserts that the output is a non-empty DataFrame with `RaceId` and `HorseId` columns, one row per race, and that no TSR gating is applied (races with no real TSR are still predicted).

Prior art: `tests/algorithms/` houses existing algorithm tests; `tests/utils/test_data.py` provides synthetic fixture-building helpers that generate the full engineered feature set. New tests should follow the same fixture pattern.

Both `ProxyTSRModel` and `ProxyTSRXGBoostAlgorithm` should have pytest test files in `tests/algorithms/`.

## Out of Scope

- Hyperparameter tuning of either the proxy TSR regressor or the downstream classifier — both use the same defaults as existing algorithms for now.
- Modifying `RatingsXGBoostAlgorithm`, `RatingsXGBoostUngatedAlgorithm`, or any other existing algorithm.
- Replacing the TSR gating in existing algorithms with proxy-based gating.
- Computing proxy TSR as a preprocessing step outside the algorithm (deferred — the separate `ProxyTSRModel` class makes this migration straightforward later).
- Extended backtesting beyond the default 60-fold window.
- Exposing `ProxyTSRModel` as a standalone CLI command or saving proxy TSR values to CSV.

## Further Notes

- The evaluations document shows that TSR-complete races are genuinely harder to call (market favourite wins only 29% of them vs the typical ~35%), yet the gated algorithm identifies genuine value at ~7.25 average winner odds. The proxy TSR strategy may not replicate this exactly on the full race population — the evaluation results will determine whether it is a net improvement or a complement to the gated approach.
- `OverallBeatenDistance` is a key input to `ProxyTSRModel`: it captures not just finishing position but how competitive a run was. Winning horses always have beaten distance = 0, while a narrow second may have higher proxy TSR than a comfortable fourth.
- `CourseName` is included as a feature to capture course-specific pace biases (e.g. Chester is tight and suits front-runners; Newmarket is a wide galloping track). This is a high-cardinality categorical; label encoding is sufficient for XGBoost.
- The `min_races` parameter (default 1) means that even a single historical run produces a proxy TSR. Setting it higher (e.g. 3 or 5) may improve reliability at the cost of NaN coverage for lightly-raced horses — this can be explored via configuration without code changes.
