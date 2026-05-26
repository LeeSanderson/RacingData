## Parent PRD

`issues/prd.md`

## What to build

Move all low-level encoding and transformation functions out of `utils/data_transforms.py` into a new `race_analytics/features/transforms.py` module. Update every caller across scripts, algorithms, and notebooks to import from the new location. Delete the now-empty source file. Write comprehensive pytest unit tests covering every encoding variant and edge case.

Functions to move: `encode_surfaces`, `encode_going`, `encode_race_type`, `calculate_speed`, `clean_weight`, `calculate_horse_count`, `calculate_weight_change`, `calculate_distance_change`.

This is a pure refactor — no behaviour changes.

## Acceptance criteria

- [ ] `race_analytics/features/transforms.py` exists and contains all moved functions
- [ ] `utils/data_transforms.py` is deleted
- [ ] No remaining imports of `utils.data_transforms` anywhere in the codebase
- [ ] `tests/features/test_transforms.py` exists with tests covering:
  - All three surface variants (AllWeather, Dirt, Turf) and an unknown surface
  - All six going categories and an unknown/unmapped going string
  - All four race types and an unknown race type
  - Speed calculation including clamping of speeds > 20 m/s to NaN
  - `clean_weight` setting WeightInPounds < 10 to NaN
  - `calculate_horse_count` grouping correctly by RaceId
  - `calculate_weight_change` and `calculate_distance_change` basic cases
- [ ] All existing tests pass

## Blocked by

None — can start immediately.

## User stories addressed

- User story 1 (feature logic in one place)
- User story 2 (identical results from notebooks and scripts)
- User story 7 (`features/` package is self-contained)
- User story 8 (old `utils/` files deleted, no shims)
- User story 16 (comprehensive unit tests for `features/` modules)
- User story 17 (existing tests refactored to new import paths)
- User story 18 (`tests/` mirrors `race_analytics/features/` structure)
