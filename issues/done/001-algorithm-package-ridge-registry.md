## Parent PRD

`issues/prd.md`

## What to build

Create the `Data/algorithms/` package containing: the shared algorithm protocol/ABC, the Ridge Regression implementation extracted from `LinearRegressionPredictor.py`, and the algorithm registry. This is the foundation that all subsequent slices build on.

The protocol defines three things: a `max_horses` constructor parameter, a `fit(train_df)` method, and a `predict(races, horse_stats, jockey_stats)` method returning one predicted winner per race. The registry exports an `ALGORITHMS` list and an `ACTIVE_ALGORITHM` reference; Ridge Regression is registered as the initial active algorithm with `max_horses=10`.

See the *Algorithm base class / protocol*, *Algorithm registry*, and *Ridge Regression algorithm* sections of the parent PRD for the precise interface contract.

## Acceptance criteria

- [ ] `Data/algorithms/__init__.py` exports `ALGORITHMS` (list of algorithm instances) and `ACTIVE_ALGORITHM` (the currently preferred instance); Ridge Regression is the active algorithm
- [ ] `Data/algorithms/base.py` defines a `Protocol` or ABC with `max_horses: int`, `fit(train_df: pd.DataFrame) -> None`, and `predict(races: pd.DataFrame, horse_stats: pd.DataFrame, jockey_stats: pd.DataFrame) -> pd.DataFrame`
- [ ] `Data/algorithms/ridge_regression.py` contains `RidgeRegressionAlgorithm` with `max_horses=10` default; Ridge + polynomial features logic is extracted from `LinearRegressionPredictor.py`
- [ ] `predict()` returns a DataFrame with exactly one row per race containing `RaceId` and `HorseId` columns — no races missing, no races duplicated
- [ ] `max_horses` filter is applied internally: races with more runners than `max_horses` are excluded before scoring
- [ ] Tests in `Data/tests/test_ridge_regression.py` verify `fit` → `predict` produces a valid winner DataFrame on a small synthetic dataset, and verify the `max_horses` filter excludes oversized races
- [ ] Tests follow the existing pattern in `test_data_analysis.py` (construct small in-memory DataFrames, assert on output — no file I/O)

## Blocked by

None — can start immediately.

## User stories addressed

- User story 14 (register algorithm via central registry)
- User story 15 (mark one algorithm as active)
- User story 16 (production predictor uses the same interface)
- User story 19 (Ridge Regression refactored into new interface)
- User story 22 (`fit` method accepting training DataFrame)
- User story 23 (`predict` method accepting race card + stats)
- User story 24 (`predict` returns one winner per race)
- User story 26 (algorithms live in a dedicated directory)
