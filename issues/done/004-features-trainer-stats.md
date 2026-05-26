## Parent PRD

`issues/prd.md`

## What to build

Move `CalculateTrainerStats` from `utils/data_analysis.py` into a new `race_analytics/features/trainer_stats.py` module. Update all callers. Delete `utils/data_analysis.py` — this is the last class remaining in that file after slices 002 and 003 have landed. Write unit tests for the trainer stats module.

## Acceptance criteria

- [ ] `race_analytics/features/trainer_stats.py` exists containing the moved `CalculateTrainerStats` class
- [ ] `utils/data_analysis.py` is deleted
- [ ] No remaining imports from `utils.data_analysis` anywhere in the codebase
- [ ] `tests/features/test_trainer_stats.py` exists with tests covering:
  - A trainer with no prior races
  - Win percentage, top-3 percentage, and average relative finishing position calculated correctly
  - Number of prior races increments correctly
  - Incremental processing: stats update correctly across multiple calls in chronological order
- [ ] All existing tests pass

## Blocked by

None — can start immediately. However, this slice is easiest to implement after `issues/002-features-race-filters.md` and `issues/003-features-horse-and-jockey-stats.md` have landed, since those remove all other classes from `utils/data_analysis.py`, leaving only `CalculateTrainerStats` to move and the file ready to delete.

## User stories addressed

- User story 1 (feature logic in one place)
- User story 4 (independently testable modules)
- User story 7 (`features/` package is self-contained)
- User story 8 (old `utils/` files deleted, no shims)
- User story 13 (trainer features wired into the model)
- User story 16 (comprehensive unit tests)
- User story 17 (existing tests refactored)
- User story 18 (`tests/` mirrors `race_analytics/features/` structure)
