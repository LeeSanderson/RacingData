## Parent PRD

`issues/prd.md`

## What to build

Update `run.ps1` to work with the new `race_analytics` package structure. The key changes are: replace the individual `pip install` lines with a single `pip install -e .`, remove the `Set-Location $RaceDataPath` step so the pipeline operates from the project root, update all nbconvert commands to reference the new notebook paths under `race_analytics/notebooks/`, and update the script invocation to call `race_analytics/scripts/predict.py` from the project root.

See the Implementation Decisions section of `issues/prd.md` for the full specification of each change.

## Acceptance criteria

- [ ] `run.ps1` contains no individual `pip install <package>` lines — dependency installation is a single `pip install -e .`
- [ ] `run.ps1` does not `Set-Location` into `Data/` before running Python steps
- [ ] nbconvert commands in `run.ps1` reference `race_analytics/notebooks/FeatureAnalysis.ipynb` (and equivalent for other notebooks)
- [ ] The converted notebook scripts are invoked from the project root; if a notebook needs the data path it receives it as an explicit argument or environment variable rather than relying on a working-directory assumption
- [ ] The prediction script is invoked as `python -m race_analytics.scripts.predict` (or equivalent) rather than `python Data/scripts/predict.py`
- [ ] `.\run.ps1` runs end-to-end without error and produces the same output files as before this slice (`Race_Features.csv`, `Horse_Stats.csv`, `Jockey_Stats.csv`, `TodaysPredictions.csv`)

## Blocked by

- Blocked by `issues/004-migrate-scripts-module.md`
- Blocked by `issues/005-migrate-notebooks.md`

## User stories addressed

- User story 7
- User story 13
