## Parent PRD

`issues/prd.md`

## What to build

Delete all Python source files (including tests and notebooks) that were left in `Data/` during the migration slices. After this slice `Data/` contains only CSV and JSON data files — its purpose as the exclusive home of C# downloader output is unambiguous.

Files to delete:
- `Data/utils/data_analysis.py`, `data_transforms.py`, `scoring.py`, `test_*.py`
- `Data/algorithms/base.py`, `ridge_regression.py`, `xgboost_algorithm.py`, `market_favourite.py`, `__init__.py`, `test_*.py`
- `Data/scripts/predict.py`, `evaluate.py`, `test_*.py`
- `Data/FeatureAnalysis.ipynb`, `HorseStatsBuilder.ipynb`, `JockeyStatsBuilder.ipynb`, `LinearRegressionPredictor.ipynb`
- Any nbconvert-generated `Data/*.py` files (e.g. `FeatureAnalysis.py`) if present

The `Data/utils/`, `Data/algorithms/`, and `Data/scripts/` subdirectories themselves may be removed if they are empty after the Python files are deleted.

## Acceptance criteria

- [ ] No `.py` or `.ipynb` files remain anywhere under `Data/` (CSV and JSON files are untouched)
- [ ] `python -m pytest tests/` passes from the project root — same count as after slice 006
- [ ] `.\run.ps1` still completes end-to-end without error after the deletion

## Blocked by

- Blocked by `issues/006-update-run-ps1.md`

## User stories addressed

- User story 9
