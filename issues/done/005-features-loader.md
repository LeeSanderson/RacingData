## Parent PRD

`issues/prd.md`

## What to build

Create `race_analytics/features/loader.py` with data loading utilities used by both the `FeaturePipeline` and scripts. The loader is responsible for returning data in chronological order — callers of `FeaturePipeline.process()` rely on this ordering guarantee. Write tests using a temporary fixture directory with synthetic CSV files.

Functions to include:
- Load historical results CSVs (globbing `Results_*.csv` files, concatenating, sorting chronologically)
- Load today's race cards (`TodaysRaceCards.csv`)
- Load pre-built stats files (`Race_Features.csv`, `Horse_Stats.csv`, `Jockey_Stats.csv`, `Trainer_Stats.csv`)

## Acceptance criteria

- [ ] `race_analytics/features/loader.py` exists with functions for all four loading cases above
- [ ] The historical results loader returns a single DataFrame sorted in ascending chronological order
- [ ] `tests/features/test_loader.py` exists with tests covering:
  - Loading multiple `Results_*.csv` files from a temporary directory, asserting rows are sorted chronologically
  - Loading today's race cards from a fixture file
  - Loading each stats file by name
  - Behaviour when a file does not exist (clear error, not a silent empty DataFrame)
- [ ] All existing tests pass

## Blocked by

None — can start immediately.

## User stories addressed

- User story 5 (loading logic separated from processing logic)
- User story 16 (comprehensive unit tests)
- User story 17 (existing tests refactored)
- User story 18 (`tests/` mirrors `race_analytics/features/` structure)
- User story 20 (loader provides utilities used by notebooks, scripts, and tests)
