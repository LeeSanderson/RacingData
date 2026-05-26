## Parent PRD

`issues/prd.md`

## What to build

Create `race_analytics/scripts/build_features.py` — a runnable script that uses `loader.py` to load all historical results in chronological order, runs `FeaturePipeline.process()`, and saves all four output CSVs: `Race_Features.csv`, `Horse_Stats.csv`, `Jockey_Stats.csv`, `Trainer_Stats.csv`.

Update `run.ps1` to replace the three `nbconvert` + `python` block pairs with a single call to this script.

This slice makes the pipeline runnable end-to-end without any notebook tooling.

## Acceptance criteria

- [ ] `race_analytics/scripts/build_features.py` exists and can be invoked as `python -m race_analytics.scripts.build_features --data <path>`
- [ ] Running the script produces all four output CSVs in the data directory: `Race_Features.csv`, `Horse_Stats.csv`, `Jockey_Stats.csv`, `Trainer_Stats.csv`
- [ ] `run.ps1` no longer contains any `nbconvert` or `FeatureAnalysis.py` / `HorseStatsBuilder.py` / `JockeyStatsBuilder.py` invocations
- [ ] `run.ps1` contains a single call to `build_features` that replaces the removed block
- [ ] Running `run.ps1` end-to-end completes without errors and produces the same four CSVs
- [ ] All existing tests pass

## Blocked by

- `issues/006-features-pipeline.md`

## User stories addressed

- User story 3 (single `build_features` call replaces `nbconvert` pattern)
- User story 11 (`Trainer_Stats.csv` produced by `build_features`)
- User story 19 (`run.ps1` updated to one script call)
