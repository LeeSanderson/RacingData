## Parent PRD

`issues/prd.md`

## What to build

Two related changes that complete the feature set:

1. **`predict.py` trainer stats merge** — Update `predict.py` to load `Trainer_Stats.csv` and merge it onto today's race cards alongside `Horse_Stats.csv` and `Jockey_Stats.csv`, so trainer features are available at prediction time.

2. **Extend `PREDICTORS` in `algorithms/base.py`** — Add the following columns to the `PREDICTORS` list used by all algorithms:
   - `Last3RaceAvgSpeed`
   - `Last3RaceSpeedTrend`
   - `Last3AvgRelFinishingPosition`
   - `TrainerNumberOfPriorRaces`
   - `TrainerWinPercentage`
   - `TrainerTop3Percentage`
   - `TrainerAvgRelFinishingPosition`

These two changes are coupled: adding trainer columns to `PREDICTORS` is only meaningful once `predict.py` merges trainer stats onto the race cards.

## Acceptance criteria

- [ ] `predict.py` loads `Trainer_Stats.csv` and merges it onto today's race cards by trainer identifier
- [ ] `TodaysPredictions.csv` is produced without error after the merge
- [ ] `PREDICTORS` in `algorithms/base.py` includes all seven new columns listed above
- [ ] `evaluate.py` runs end-to-end without error with the expanded `PREDICTORS` set (NaN values for horses with fewer than 3 prior races are handled by existing imputation logic)
- [ ] Running `run.ps1` end-to-end completes without errors and produces `TodaysPredictions.csv` with predictions influenced by the new features
- [ ] All existing tests pass

## Blocked by

- `issues/007-build-features-script.md` (must produce `Trainer_Stats.csv` before `predict.py` can load it)

## User stories addressed

- User story 10 (`predict.py` merges trainer stats)
- User story 11 (`Trainer_Stats.csv` available at prediction time)
- User story 12 (`Last3Race*` features added to `PREDICTORS`)
- User story 13 (trainer features added to `PREDICTORS`)
