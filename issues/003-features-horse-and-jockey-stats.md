## Parent PRD

`issues/prd.md`

## What to build

Move `CalculateHorsesStats` and `CalculateJockeyStats` from `utils/data_analysis.py` into dedicated modules `race_analytics/features/horse_stats.py` and `race_analytics/features/jockey_stats.py`. Update all callers. As part of this slice, remove the private `_compute_horse_stats()` and `_compute_jockey_stats()` methods from `evaluate.py` and replace them with calls to the new shared modules. Write unit tests for both modules.

`utils/data_analysis.py` still contains `CalculateTrainerStats` at this point and is not deleted here.

## Acceptance criteria

- [ ] `race_analytics/features/horse_stats.py` exists containing the moved `CalculateHorsesStats` class
- [ ] `race_analytics/features/jockey_stats.py` exists containing the moved `CalculateJockeyStats` class
- [ ] `evaluate.py` no longer contains `_compute_horse_stats()` or `_compute_jockey_stats()` methods; it delegates entirely to the new modules
- [ ] No remaining imports of these classes from `utils.data_analysis`
- [ ] `tests/features/test_horse_stats.py` exists with tests covering:
  - A horse with no prior races (all stats should be NaN/zero)
  - A horse with one prior race (last-race features populated, 3-race aggregates NaN)
  - A horse with three or more prior races (all features including `Last3RaceAvgSpeed`, `Last3RaceSpeedTrend`, `Last3AvgRelFinishingPosition` populated)
  - Incremental processing: stats update correctly across multiple calls in chronological order
- [ ] `tests/features/test_jockey_stats.py` exists with tests covering:
  - A jockey with no prior races
  - Win percentage, top-3 percentage, and average relative finishing position calculated correctly
  - `DaysSinceJockeyLastRaced` calculated correctly
  - Incremental processing across multiple calls
- [ ] Walk-forward evaluation in `evaluate.py` produces the same output before and after this refactor (verified by running the evaluate script against fixture data)
- [ ] All existing tests pass

## Blocked by

None — can start immediately.

## User stories addressed

- User story 1 (feature logic in one place)
- User story 4 (independently testable modules)
- User story 7 (`features/` package is self-contained)
- User story 8 (old `utils/` files deleted, no shims)
- User story 9 (`evaluate.py` delegates to `features/`)
- User story 16 (comprehensive unit tests)
- User story 17 (existing tests refactored)
- User story 18 (`tests/` mirrors `race_analytics/features/` structure)
