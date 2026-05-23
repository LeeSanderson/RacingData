## Parent PRD

`issues/prd.md`

## What to build

Create a `pyproject.toml` at the project root that declares all Python runtime dependencies and configures pytest. Create the empty `race_analytics/` package skeleton (top-level and all subpackage `__init__.py` files) and the `tests/` directory structure. No source files are moved yet — this slice makes the package installable and pytest discoverable end-to-end.

## Acceptance criteria

- [ ] `pyproject.toml` exists at the project root with `name = "race_analytics"`, all runtime dependencies declared (pandas, numpy, scikit-learn, xgboost, python-dateutil, matplotlib, ipykernel, nbconvert), and pytest configured with `testpaths = ["tests"]` and `pythonpath = ["."]`
- [ ] `pip install -e .` runs without error from the project root
- [ ] `race_analytics/__init__.py`, `race_analytics/utils/__init__.py`, `race_analytics/algorithms/__init__.py`, `race_analytics/scripts/__init__.py`, and `race_analytics/notebooks/__init__.py` all exist (may be empty)
- [ ] `tests/`, `tests/utils/`, `tests/algorithms/`, and `tests/scripts/` directories exist (with `__init__.py` or bare — whichever pytest requires)
- [ ] `python -m pytest tests/` runs from the project root without collection errors (zero tests collected is acceptable at this stage)

## Blocked by

None — can start immediately.

## User stories addressed

- User story 2
- User story 6
- User story 12
