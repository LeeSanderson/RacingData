## Parent PRD

`issues/prd.md`

## What to build

Create `Data/predict.py` — the production prediction script described in the *Production prediction script (predict.py)* section of the parent PRD. This script eventually replaces the `LinearRegressionPredictor` notebook conversion step in `run.ps1` (that wiring is handled separately in `issues/006-run-ps1-wiring.md`).

The script reads the four pre-computed files already produced by earlier `run.ps1` steps — `Race_Features.csv`, `Horse_Stats.csv`, `Jockey_Stats.csv`, and `TodaysRaceCards.csv` — with no in-memory feature recomputation. It fetches the active algorithm from the registry, calls `fit` with the training features, calls `predict` with today's race card data and stats, and writes `TodaysPredictions.csv` in the existing format so the downstream `validate` CLI step continues to work unchanged.

## Acceptance criteria

- [ ] Running `python Data/predict.py --data <DataPath>` (or equivalent argument convention) produces `TodaysPredictions.csv` with columns: `RaceId`, `CourseId`, `CourseName`, `Off`, `HorseId`, `HorseName`
- [ ] The active algorithm is read from the registry — swapping `ACTIVE_ALGORITHM` in `Data/algorithms/__init__.py` changes which algorithm runs without modifying `predict.py`
- [ ] The script reads only from the four pre-computed feature files; it does not re-run feature engineering
- [ ] Output column schema and row format are identical to what `LinearRegressionPredictor.py` currently produces so that the `validate` CLI step works without modification
- [ ] The script can be run in isolation (outside of `run.ps1`) for manual testing

## Blocked by

- Blocked by `issues/001-algorithm-package-ridge-registry.md`

## User stories addressed

- User story 16 (production predictor uses the same algorithm interface as the evaluation pipeline)
- User story 17 (production predictor reads pre-computed feature files; no increased run time)
- User story 18 (production predictor continues writing `TodaysPredictions.csv`)
- User story 25 (data preparation logic separated from algorithm logic)
