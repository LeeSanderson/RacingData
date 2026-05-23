## Parent PRD

`issues/prd.md`

## What to build

Move all algorithm source files from `Data/algorithms/` into `race_analytics/algorithms/` and their tests into `tests/algorithms/`. Update all imports to use fully-qualified `race_analytics.*` references. Remove `sys.path.insert` hacks. The algorithm registry in `race_analytics/algorithms/__init__.py` must remain the single place where algorithms are listed and the active one is declared — its internal structure is preserved, only import paths change. The files in `Data/algorithms/` are left in place until `issues/007-remove-old-data-python-source.md`.

Files to move:
- `Data/algorithms/base.py` → `race_analytics/algorithms/base.py`
- `Data/algorithms/ridge_regression.py` → `race_analytics/algorithms/ridge_regression.py`
- `Data/algorithms/xgboost_algorithm.py` → `race_analytics/algorithms/xgboost_algorithm.py`
- `Data/algorithms/market_favourite.py` → `race_analytics/algorithms/market_favourite.py`
- `Data/algorithms/__init__.py` → `race_analytics/algorithms/__init__.py` (overwrite the stub from slice 001)
- `Data/algorithms/test_ridge_regression.py` → `tests/algorithms/test_ridge_regression.py`
- `Data/algorithms/test_xgboost_algorithm.py` → `tests/algorithms/test_xgboost_algorithm.py`
- `Data/algorithms/test_market_favourite.py` → `tests/algorithms/test_market_favourite.py`

## Acceptance criteria

- [ ] All algorithm source files exist under `race_analytics/algorithms/` with imports updated to `from race_analytics.algorithms.X import …` and `from race_analytics.utils.X import …`
- [ ] All three test files exist under `tests/algorithms/` with no `sys.path.insert` lines
- [ ] `race_analytics/algorithms/__init__.py` registers the same algorithms as the original and designates the same active algorithm — only import paths are changed
- [ ] `python -m pytest tests/algorithms/` passes from the project root with the same number of passing tests as before this slice
- [ ] No new test files or test logic are added — only moves and import updates

## Blocked by

- Blocked by `issues/002-migrate-utils-module.md`

## User stories addressed

- User story 1
- User story 3
- User story 5
- User story 8
- User story 9
- User story 11
