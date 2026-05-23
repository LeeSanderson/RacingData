## Parent PRD

`issues/prd.md`

## What to build

Move `predict.py` and `evaluate.py` from `Data/scripts/` into `race_analytics/scripts/` and their tests into `tests/scripts/`. Update all imports to use fully-qualified `race_analytics.*` references. Remove `sys.path.insert` hacks. The files in `Data/scripts/` are left in place until `issues/007-remove-old-data-python-source.md`.

Files to move:
- `Data/scripts/predict.py` → `race_analytics/scripts/predict.py`
- `Data/scripts/evaluate.py` → `race_analytics/scripts/evaluate.py`
- `Data/scripts/test_predict.py` → `tests/scripts/test_predict.py`
- `Data/scripts/test_evaluate.py` → `tests/scripts/test_evaluate.py`

## Acceptance criteria

- [ ] Both script files exist under `race_analytics/scripts/` with imports updated to `from race_analytics.algorithms.X import …`, `from race_analytics.utils.X import …`, etc.
- [ ] Both test files exist under `tests/scripts/` with no `sys.path.insert` lines
- [ ] `python -m pytest tests/scripts/` passes from the project root with the same number of passing tests as before this slice
- [ ] `python -m race_analytics.scripts.predict` (or equivalent entry-point invocation) runs without import errors when given valid input
- [ ] No new test files or test logic are added — only moves and import updates

## Blocked by

- Blocked by `issues/003-migrate-algorithms-module.md`

## User stories addressed

- User story 1
- User story 3
- User story 5
- User story 8
- User story 9
