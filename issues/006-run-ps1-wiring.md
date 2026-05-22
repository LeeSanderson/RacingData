## Parent PRD

`issues/prd.md`

## What to build

Update `run.ps1` to replace the `LinearRegressionPredictor` notebook conversion and execution steps with a call to `predict.py`, and add `xgboost` to the `pip install` invocation. All other steps (`FeatureAnalysis`, `HorseStatsBuilder`, `JockeyStatsBuilder`, `todaysracecards`, `validate`) remain unchanged. See the *run.ps1 changes* section of the parent PRD.

This slice is deliberately deferred until after XGBoost has been evaluated via `evaluate.py` (`issues/005-xgboost-algorithm.md`), so that the algorithm comparison informs whether Ridge Regression should remain the active algorithm before production wiring is changed.

## Acceptance criteria

- [ ] `run.ps1` replaces the nbconvert conversion and execution of `LinearRegressionPredictor.ipynb` (or `.py`) with `python Data/predict.py --data $DataPath` (or equivalent)
- [ ] `xgboost` is added to the `pip install` line in `run.ps1`
- [ ] Running `.\run.ps1` end-to-end completes successfully and produces `TodaysPredictions.csv` via the new `predict.py` path
- [ ] The `validate` CLI step (which scores `TodaysPredictions.csv` against actual results) continues to pass
- [ ] `FeatureAnalysis`, `HorseStatsBuilder`, `JockeyStatsBuilder`, and `todaysracecards` steps are unmodified

## Blocked by

- Blocked by `issues/004-predict-py.md`
- Blocked by `issues/005-xgboost-algorithm.md`

## User stories addressed

- User story 18 (daily production predictor continues writing `TodaysPredictions.csv`; `validate` step works without changes)
