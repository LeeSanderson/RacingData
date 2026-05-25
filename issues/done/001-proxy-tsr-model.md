## Parent PRD

`issues/prd.md`

## What to build

A standalone `ProxyTSRModel` class that trains an XGBoost regressor to predict Racing Post's `TopSpeedRating` from per-race outcome data, then aggregates predictions per horse into three summary statistics used as features downstream.

The class must:
- Accept a `min_races: int = 1` constructor parameter controlling the minimum race history required before a horse receives a non-NaN proxy rating.
- Expose a `fit(train_df)` method that trains the regressor on all rows in `train_df` where `TopSpeedRating` is not NaN, using the features described in the PRD's Implementation Decisions: `Speed`, `DistanceInMeters`, `WeightInPounds`, `HorseCount`, already-encoded surface/going/race-type columns, `CourseName` (label-encoded integer with a safe fallback for unseen courses), `FinishingPosition`, `OverallBeatenDistance`.
- Expose a `compute_horse_proxy_tsr(train_df) -> DataFrame` method that applies the fitted regressor to every row in `train_df` (including rows without a real TSR), then groups by `HorseId` to produce three columns: `PeakProxyTSR` (all-time best predicted value), `LastProxyTSR` (most recent race), `Best5ProxyTSR` (best across last 5 races, ordered by `Off` date). Horses below the `min_races` threshold receive NaN across all three columns.

See the Implementation Decisions section of the PRD for full feature and interface details.

## Acceptance criteria

- [ ] `ProxyTSRModel(min_races=1).fit(train_df)` completes without error on a synthetic DataFrame that contains a mix of rows with and without `TopSpeedRating`.
- [ ] `compute_horse_proxy_tsr(train_df)` returns a DataFrame with exactly the columns `HorseId`, `PeakProxyTSR`, `LastProxyTSR`, `Best5ProxyTSR`.
- [ ] Horses whose race count is below `min_races` have NaN for all three proxy columns.
- [ ] `Best5ProxyTSR <= PeakProxyTSR` holds for all non-NaN rows (best-of-5 cannot exceed all-time best).
- [ ] `LastProxyTSR` reflects the horse's most recent race (highest `Off` date), not an arbitrary row.
- [ ] An unseen `CourseName` at predict time does not raise an exception (safe fallback encoding).
- [ ] `fit` raises a clear error (or returns gracefully) if called on a DataFrame with no rows where `TopSpeedRating` is not NaN.
- [ ] Unit tests covering the above live in `tests/algorithms/test_proxy_tsr.py` using the synthetic fixture helpers from `tests/utils/test_data.py`.

## Blocked by

None — can start immediately.

## User stories addressed

- User story 3 — proxy TSR provides a speed signal for horses without a Racing Post TSR
- User story 4 — normalises for race conditions (surface, going, distance, course)
- User story 7 — computation encapsulated in a standalone, reusable class
- User story 8 — `min_races` configuration parameter with default of 1
- User story 13 — `CourseName` label-encoded with safe fallback for unseen courses
