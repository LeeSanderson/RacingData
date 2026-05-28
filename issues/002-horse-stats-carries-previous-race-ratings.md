# Issue 002: `Horse_Stats.csv` carries previous-race ratings

## Parent PRD

`issues/prd.md`

## What to build

Extend `extract_horse_stats` (`race_analytics/features/horse_stats.py`) so the
per-horse serving table carries the horse's most-recent completed race ratings as
`LastRaceOfficialRating`, `LastRaceRacingPostRating` and `LastRaceTopSpeedRating`.
This is the serving-side half of the previous-race rating definition described in
the PRD's "Rating features become previous-race values" decision.

`extract_horse_stats` already takes the horse's most recent race (`last`) and
renames its raw columns (e.g. `Speed → LastRaceSpeed`). Add `OfficialRating`,
`RacingPostRating`, `TopSpeedRating` to that rename map so the most-recent race's
ratings become the `LastRace*` rating values for today — consistent in meaning
with the training-side `LastRace*` ratings that `CalculateHorsesStats` already
produces in `Race_Features.csv` (no change needed to the processor).

`FeaturePipeline.save_horse_stats` already calls `extract_horse_stats`, so the new
columns flow into `Horse_Stats.csv` automatically when `build_features` runs — no
other wiring needed. This is the blocker for the algorithm slices (003, 004),
which will source ratings from this stats join.

## Acceptance criteria

- [ ] `extract_horse_stats(...)` output includes `LastRaceOfficialRating`,
      `LastRaceRacingPostRating` and `LastRaceTopSpeedRating`, each equal to the
      horse's most-recent completed race rating
- [ ] `python -m race_analytics.scripts.build_features --data Data` writes a
      `Horse_Stats.csv` containing the three new columns without erroring
- [ ] `tests/features/test_horse_stats.py` gains a test asserting the three
      `LastRace*` rating columns are present in `extract_horse_stats` output and
      hold the most-recent race's rating values (following the existing fixture
      style, e.g. the `four_day_df` / `_secret_on` pattern)
- [ ] No change to the append-only monthly `Results_*.csv` schema; the change to
      `Horse_Stats.csv` is purely additive

## Blocked by

None - can start immediately.

## User stories addressed

Reference by number from the parent PRD:

- User story 4
- User story 6
- User story 5 (serving-side half — identical definition in training and serving)
