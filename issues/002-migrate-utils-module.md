## Parent PRD

`issues/prd.md`

## What to build

Move all utility source files from `Data/utils/` into `race_analytics/utils/` and their corresponding tests from `Data/utils/test_*.py` into `tests/utils/`. Update every import inside the moved files to use fully-qualified `race_analytics.utils.*` references. Remove all `sys.path.insert` hacks. The files in `Data/utils/` are left in place until `issues/007-remove-old-data-python-source.md`.

Files to move:
- `Data/utils/data_analysis.py` → `race_analytics/utils/data_analysis.py`
- `Data/utils/data_transforms.py` → `race_analytics/utils/data_transforms.py`
- `Data/utils/scoring.py` → `race_analytics/utils/scoring.py`
- `Data/utils/test_data.py` → `tests/utils/test_data.py`
- `Data/utils/test_data_analysis.py` → `tests/utils/test_data_analysis.py`
- `Data/utils/test_data_transforms.py` → `tests/utils/test_data_transforms.py`
- `Data/utils/test_scoring.py` → `tests/utils/test_scoring.py`

## Acceptance criteria

- [ ] All four utility source files exist under `race_analytics/utils/` with imports updated to `from race_analytics.utils.X import …`
- [ ] All four test files exist under `tests/utils/` with no `sys.path.insert` lines
- [ ] `python -m pytest tests/utils/` passes from the project root with the same number of passing tests as before this slice
- [ ] No new test files or test logic are added — only moves and import updates

## Blocked by

- Blocked by `issues/001-create-pyproject-and-package-skeleton.md`

## User stories addressed

- User story 1
- User story 3
- User story 5
- User story 8
- User story 9
