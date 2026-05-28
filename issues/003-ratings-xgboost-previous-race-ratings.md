# Issue 003: `RatingsXGBoost` reads previous-race ratings from the stats join

## Parent PRD

`issues/prd.md`

## What to build

Make `RatingsXGBoostAlgorithm` and its ungated variant
(`RatingsXGBoostUngatedAlgorithm`) use **previous-race** ratings sourced entirely
from the per-horse stats join, never from the race card. See the PRD's
"`RatingsXGBoostAlgorithm` (and ungated variant)" implementation decision.

In `race_analytics/algorithms/ratings_xgboost.py`:

- Replace the current-race `RATING_COLS = ["OfficialRating", "RacingPostRating",
  "TopSpeedRating"]` with the `LastRace*` rating columns
  (`LastRaceOfficialRating`, `LastRaceRacingPostRating`, `LastRaceTopSpeedRating`)
  for both the absolute features and the `Rel*` field-relative derivatives
  (`Rel* = value − race-mean of that previous-race rating`).
- In `predict()`, the rating features now arrive via the existing `horse_stats`
  merge (issue 002 puts them in `Horse_Stats.csv`); no rating column is read from
  the `races` card argument.
- Redefine the `require_tsr` gate to require every horse in a race to have a
  non-null `LastRaceTopSpeedRating` (instead of current-race `TopSpeedRating`).
  Keep both the gated `RatingsXGBoostAlgorithm` and ungated
  `RatingsXGBoostUngatedAlgorithm` registered for comparison.

`fit()` reads `LastRace*` ratings from `train_df` (present via
`CalculateHorsesStats` in the engineered features). Both variants stay in the
`ALGORITHMS` registry; no `ACTIVE_ALGORITHM` change here (that is issue 007).

## Acceptance criteria

- [ ] After `fit()`, the algorithm's selected feature columns contain the
      `LastRace*` rating columns (absolute + `Rel*`) and **no** current-race
      rating column (`OfficialRating`/`RacingPostRating`/`TopSpeedRating`)
- [ ] `predict()` derives rating features only from the `horse_stats` argument; a
      `races` card without rating columns still yields predictions
- [ ] The `require_tsr` gate filters on `LastRaceTopSpeedRating` coverage — a test
      shows a race with a null `LastRaceTopSpeedRating` is excluded by the gated
      variant but kept by the ungated variant
- [ ] `tests/algorithms/test_predictors.py` (or a dedicated test) is extended to
      assert the above, following the existing synthetic-frame style
- [ ] `python -m race_analytics.scripts.evaluate --folds 2 --training-months 2
      --algorithms RatingsXGBoostAlgorithm,RatingsXGBoostUngatedAlgorithm` runs
      end-to-end without erroring

## Blocked by

- Blocked by `issues/002-horse-stats-carries-previous-race-ratings.md`

## User stories addressed

Reference by number from the parent PRD:

- User story 3
- User story 5
- User story 7
- User story 8
- User story 9
- User story 10
- User story 21 (behaviour tests for this slice)
