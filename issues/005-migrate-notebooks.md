## Parent PRD

`issues/prd.md`

## What to build

Move all Jupyter notebooks from `Data/` into `race_analytics/notebooks/` and update their internal imports to use fully-qualified `race_analytics.*` references. Update `.gitignore` so that nbconvert-generated `.py` files at the new location are excluded. The original notebook files in `Data/` are left in place until `issues/007-remove-old-data-python-source.md`.

Notebooks to move:
- `Data/FeatureAnalysis.ipynb` → `race_analytics/notebooks/FeatureAnalysis.ipynb`
- `Data/HorseStatsBuilder.ipynb` → `race_analytics/notebooks/HorseStatsBuilder.ipynb`
- `Data/JockeyStatsBuilder.ipynb` → `race_analytics/notebooks/JockeyStatsBuilder.ipynb`
- `Data/LinearRegressionPredictor.ipynb` → `race_analytics/notebooks/LinearRegressionPredictor.ipynb`

Note: after this slice `run.ps1` still references `Data/` paths — that is corrected in `issues/006-update-run-ps1.md`.

## Acceptance criteria

- [ ] All four notebooks exist under `race_analytics/notebooks/` with internal import cells updated to `from race_analytics.utils.X import …` etc.
- [ ] `.gitignore` includes a pattern covering `race_analytics/notebooks/*.py` (nbconvert output at the new location)
- [ ] The existing `.gitignore` pattern for `Data/*.py` is retained (covers any legacy nbconvert output still in `Data/`)
- [ ] Notebooks can be opened in Jupyter without import errors when the package is installed via `pip install -e .`

## Blocked by

- Blocked by `issues/003-migrate-algorithms-module.md`

## User stories addressed

- User story 4
- User story 10
