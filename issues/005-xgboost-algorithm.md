## Parent PRD

`issues/prd.md`

## What to build

Implement `XGBoostAlgorithm` under the shared algorithm interface and add it to the registry alongside Ridge Regression. See the *XGBoost algorithm* section of the parent PRD. Once registered, running `evaluate.py` will automatically include it in the comparison without any changes to the evaluation script.

The algorithm must accept a configurable `max_horses` parameter and apply it internally, consistent with user story 21. Ridge Regression remains the active algorithm; XGBoost is added to the `ALGORITHMS` list only.

## Acceptance criteria

- [ ] `Data/algorithms/xgboost_algorithm.py` contains `XGBoostAlgorithm` implementing the same protocol as `RidgeRegressionAlgorithm`
- [ ] `XGBoostAlgorithm` accepts a `max_horses` constructor parameter; races with more runners than `max_horses` are excluded internally
- [ ] `predict()` returns exactly one `RaceId`/`HorseId` row per race — no races missing, no races duplicated
- [ ] `XGBoostAlgorithm` is added to the `ALGORITHMS` list in `Data/algorithms/__init__.py`; `ACTIVE_ALGORITHM` remains Ridge Regression
- [ ] Running `python Data/evaluate.py` prints results for both Ridge Regression and XGBoost without any changes to `evaluate.py`
- [ ] `Data/tests/test_xgboost_algorithm.py` passes the same algorithm contract tests as `test_ridge_regression.py` (valid winner DataFrame, `max_horses` filter)
- [ ] Tests use a fixed random seed so results are deterministic

## Blocked by

- Blocked by `issues/001-algorithm-package-ridge-registry.md`
- Blocked by `issues/003-evaluate-py.md` (XGBoost should only be added once evaluate.py is working and Ridge Regression results have been observed)

## User stories addressed

- User story 20 (XGBoost algorithm implemented under the new interface)
- User story 21 (XGBoost has a configurable maximum field size)
- User story 22 (`fit` method accepting a training DataFrame)
- User story 23 (`predict` method accepting race card data plus stats)
- User story 24 (`predict` returns exactly one predicted winner per race)
