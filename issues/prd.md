# PRD: Restructure Python ML Layer as a Proper Package

## Problem Statement

The Python ML layer lives inside `Data/`, a directory whose primary purpose is to hold raw CSV and JSON data files produced by the C# downloader. This mixing creates several problems for a developer working on the pipeline:

- Navigating to Python source files means scrolling past 76 CSV/JSON data files in the same directory
- Importing across the three sub-packages (`utils`, `algorithms`, `scripts`) requires `sys.path.insert` hacks at the top of every script and test file
- Dependencies (pandas, numpy, scikit-learn, xgboost, etc.) are not declared anywhere — they are installed ad-hoc by `run.ps1` with individual `pip install` commands
- Jupyter notebooks live next to data files rather than next to the code they depend on
- Running pytest requires explicitly listing each subdirectory (`pytest Data/utils/ Data/algorithms/ Data/scripts/`) because there is no package-level test root
- There is no `pyproject.toml`, so the project cannot be installed as a package and IDEs cannot index it properly

## Solution

Restructure the Python ML layer as a proper Python package called `race_analytics` at the project root, fully separated from the `Data/` folder. Add a `pyproject.toml` that declares dependencies and configures pytest. Move tests into a separate top-level `tests/` directory that mirrors the package structure. The `Data/` folder is left untouched — it remains the exclusive home of CSV and JSON files written by the C# downloader.

The target layout:

```
RacingData/
├── race_analytics/
│   ├── __init__.py
│   ├── algorithms/      # algorithm implementations
│   ├── utils/           # data utilities
│   ├── scripts/         # predict.py and evaluate.py
│   └── notebooks/       # Jupyter notebooks
├── tests/
│   ├── algorithms/
│   ├── utils/
│   └── scripts/
├── pyproject.toml
└── Data/                # unchanged — C# downloader writes here
```

## User Stories

1. As a developer, I want to import from `race_analytics.utils` without `sys.path` hacks, so that cross-module imports are clean, reliable, and IDE-navigable.
2. As a developer, I want a `pyproject.toml`, so that all Python dependencies are declared in one place and can be installed with `pip install -e .`.
3. As a developer, I want Python source code separated from CSV and JSON data files, so that navigating to code is not cluttered by data.
4. As a developer, I want notebooks inside `race_analytics/notebooks/`, so that they sit next to the utilities and algorithms they import from.
5. As a developer, I want tests in a separate `tests/` directory mirroring the package structure, so that the `race_analytics` package has clean boundaries with no test code inside it.
6. As a developer, I want to run `python -m pytest tests/` from the project root, so that I do not need to enumerate individual subdirectories.
7. As a developer, I want `run.ps1` to reference the new notebook and script paths, so that the full end-to-end pipeline continues to work after the restructure.
8. As a developer, I want all `sys.path.insert` hacks removed from scripts and tests, so that imports rely entirely on the properly installed package.
9. As a developer, I want the `Data/` directory to contain only data files (CSV, JSON), so that its purpose is unambiguous and no Python source is accidentally committed there.
10. As a developer, I want the `.gitignore` updated to exclude nbconvert-generated `.py` files at their new location, so that generated artefacts are not accidentally committed.
11. As a developer, I want the algorithm registry (`algorithms/__init__.py`) to remain the single place where algorithms are listed and the active one is declared, so that `predict.py` and `evaluate.py` do not need to change their registry logic.
12. As a developer, I want pytest configured in `pyproject.toml` with `testpaths` and `pythonpath` settings, so that running `pytest` from the project root discovers all tests without extra flags.
13. As a developer, I want the `run.ps1` pip-install block replaced by a single `pip install -e .` call, so that the dependency list is maintained in one place rather than scattered across the script.

## Implementation Decisions

- The package is named `race_analytics` to avoid confusion with the existing C# `RacePredictor` namespace.
- Flat layout: `race_analytics/` lives directly at the project root (no `src/` wrapper).
- All algorithm, utility, and script source files move from their `Data/` subdirectories into the corresponding `race_analytics/` subdirectory.
- All test files move to a top-level `tests/` directory, mirroring the package structure: `tests/algorithms/`, `tests/utils/`, `tests/scripts/`.
- Notebooks move from `Data/` to `race_analytics/notebooks/` so they are co-located with the package code they import.
- A `pyproject.toml` is introduced with the package name, declared runtime dependencies (pandas, numpy, scikit-learn, xgboost, python-dateutil, matplotlib, ipykernel, nbconvert), and pytest configuration (`testpaths = ["tests"]`, `pythonpath = [".""]`).
- All internal imports are updated from bare module references (`from utils.X import …`) to fully-qualified package references (`from race_analytics.utils.X import …`).
- All `sys.path.insert` hacks are removed from scripts and test files — the installed package resolves imports instead.
- `run.ps1` is updated to:
  - Replace individual `pip install` lines with `pip install -e .`
  - Remove the `Set-Location $RaceDataPath` step and operate from the project root
  - Update `nbconvert` commands to reference the new notebook paths under `race_analytics/notebooks/`
  - Run converted notebook scripts from the project root (passing `Data/` as the data path argument where needed)
  - Invoke `race_analytics/scripts/predict.py` via `python -m race_analytics.scripts.predict` or equivalent
- The `.gitignore` pattern that excludes nbconvert-generated `.py` files is updated to cover the new notebook location.
- The `Data/` folder is left entirely untouched: its subdirectories (`algorithms/`, `utils/`, `scripts/`) and the notebooks at its root are deleted only after the new structure is verified.

## Testing Decisions

- This is a pure structural refactor — no new behaviour is introduced, so no new tests are written as part of this PRD.
- All existing tests are moved, not rewritten. Each test file moves from `Data/<subpackage>/test_*.py` to `tests/<subpackage>/test_*.py`.
- Tests follow the existing pattern: construct a small in-memory DataFrame, call the function under test, assert on the output. No mocking of the filesystem or external data.
- After migration, correctness is verified by running `python -m pytest tests/` from the project root and confirming all previously-passing tests still pass.
- End-to-end pipeline correctness is verified by running `.\run.ps1` and confirming it completes without error.
- No new pytest fixtures or conftest files are required unless a test currently relies on a `sys.path` hack that needs replacing with a fixture.

## Out of Scope

- Adding tests for currently-untested code (separate PRD)
- Changes to algorithm implementations, feature engineering logic, or data transforms
- Changes to C# projects (`RacePredictor.Core`, `RaceDataDownloader`)
- Changes to CSV schemas or the data produced by the C# downloader
- Type annotations, docstrings, or other code-quality improvements
- Publishing the package to PyPI

## Further Notes

- The nbconvert-generated `.py` files (e.g. `FeatureAnalysis.py`) are currently gitignored via a pattern matching `Data/*.py`. After notebooks move to `race_analytics/notebooks/`, this pattern must be updated to also ignore `race_analytics/notebooks/*.py`.
- The `run.ps1` currently changes directory to `Data/` before running converted notebook scripts — the notebooks assume they are run from `Data/` when constructing relative paths to CSV files. After migration, either the notebooks must be updated to use an absolute or configurable data path, or `run.ps1` must pass the data path explicitly.
- Installing the package with `pip install -e .` in development mode means any change to `race_analytics/` source is immediately reflected without reinstalling.
