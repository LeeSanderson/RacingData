## Parent PRD

`issues/prd.md`

## What to build

Simplify the `FeatureAnalysis`, `HorseStatsBuilder`, and `JockeyStatsBuilder` notebooks so they use `FeaturePipeline` and `loader.py` for load/process/save rather than reimplementing feature engineering inline. The notebooks remain in the repository as interactive visualisation tools — their sole change is that the data preparation cells are replaced with `FeaturePipeline` calls, leaving the analysis/visualisation cells intact.

The `.py` nbconvert outputs remain gitignored and are no longer used by `run.ps1`.

## Acceptance criteria

- [ ] `FeatureAnalysis.ipynb` loads data via `loader.py` and processes it via `FeaturePipeline` rather than calling encoding and stats functions directly
- [ ] `HorseStatsBuilder.ipynb` no longer reimplements rolling-average logic; it reads `Race_Features.csv` (or calls the pipeline) and delegates all stat computation to the shared modules
- [ ] `JockeyStatsBuilder.ipynb` no longer reimplements jockey percentage logic; it delegates to the shared modules
- [ ] All three notebooks execute without errors from top to bottom in a clean kernel
- [ ] The visualisation and analysis cells in each notebook are unchanged
- [ ] No inline duplication of encoding, rolling-average, or days-calculation logic remains in any notebook

## Blocked by

- `issues/007-build-features-script.md`

## User stories addressed

- User story 14 (notebooks remain for interactive exploration)
- User story 15 (notebooks call `FeaturePipeline` for load/process/save)
