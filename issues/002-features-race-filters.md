## Parent PRD

`issues/prd.md`

## What to build

Move `CalculateRacesWithKnownHorsesAndJockeys` from `utils/data_analysis.py` into a new `race_analytics/features/race_filters.py` module. Update all callers to import from the new location. Write unit tests that construct minimal DataFrames and assert the filter flags are set correctly.

This is a pure refactor — no behaviour changes. `utils/data_analysis.py` still contains other classes at this point and is not deleted here.

## Acceptance criteria

- [ ] `race_analytics/features/race_filters.py` exists and contains the moved class
- [ ] No remaining imports of `CalculateRacesWithKnownHorsesAndJockeys` from `utils.data_analysis`
- [ ] `tests/features/test_race_filters.py` exists with tests covering:
  - A race where all horses and jockeys have prior history (should be marked as known)
  - A race where at least one horse has no prior history (should be marked as unknown)
  - A race where at least one jockey has no prior history (should be marked as unknown)
  - Incremental processing: marking updates correctly as prior data accumulates across multiple calls
- [ ] All existing tests pass

## Blocked by

None — can start immediately.

## User stories addressed

- User story 1 (feature logic in one place)
- User story 4 (independently testable modules)
- User story 7 (`features/` package is self-contained)
- User story 8 (old `utils/` files deleted, no shims)
- User story 16 (comprehensive unit tests)
- User story 17 (existing tests refactored)
- User story 18 (`tests/` mirrors `race_analytics/features/` structure)
