# PRD: Feature Engineering Refactor

## Problem Statement

The Python ML pipeline's feature engineering logic is duplicated across multiple notebooks, scripts, and utility modules. The same encoding functions, rolling statistics calculations, and days-since-last-race computations appear in three to four separate locations with subtle divergences between them. This makes the codebase hard to maintain, creates a risk of inconsistent results between training, evaluation, and prediction, and forces the pipeline to use `nbconvert` to convert notebooks into scripts before running them — a fragile pattern that conflates exploration tooling with production data processing. Additionally, several computed features (`Last3RaceAvgSpeed`, `Last3RaceSpeedTrend`, `Last3AvgRelFinishingPosition`, and all trainer statistics) are never passed to the algorithms, leaving potentially valuable signal on the table.

## Solution

Consolidate all feature engineering logic into a dedicated `race_analytics/features/` package containing focused, independently-testable modules. A thin `FeaturePipeline` orchestrator delegates to these modules and handles both batch (historical) and incremental (walk-forward) processing through a single stateful interface. A new `build_features` script replaces the `nbconvert` pattern in `run.ps1`, producing all required output CSVs in one invocation. Notebooks are simplified to use `FeaturePipeline` for load/process/save, retaining their value as interactive visualisation tools. All previously unused features are wired into the model's predictor set, and trainer statistics are promoted to first-class status alongside horse and jockey statistics.

## User Stories

1. As a developer, I want feature engineering logic to live in one place, so that a bug fix or improvement is made once and applies everywhere.
2. As a developer, I want to import `FeaturePipeline` in a notebook or a script with identical results, so that I can trust that training, evaluation, and prediction use the same feature definitions.
3. As a developer, I want to run `build_features` as a single script, so that I do not need `nbconvert` installed or notebooks converted to `.py` files before the pipeline can run.
4. As a developer, I want each feature engineering module (`transforms`, `horse_stats`, `jockey_stats`, `trainer_stats`, `race_filters`) to be independently testable, so that I can verify correctness in isolation without running the full pipeline.
5. As a developer, I want the data loading utilities separated from the processing logic, so that tests can construct DataFrames directly without needing to touch the filesystem.
6. As a developer, I want the `FeaturePipeline` to accept data in chronological order and accumulate state across calls, so that the same interface works for both a single batch run and a day-by-day walk-forward loop.
7. As a developer, I want the `features/` package to be self-contained, so that I can understand the full feature engineering story by reading one directory.
8. As a developer, I want the old `utils/data_transforms.py` and `utils/data_analysis.py` files deleted rather than shimmed, so that there is only one canonical import path for each function.
9. As a developer, I want the `evaluate.py` script to delegate horse and jockey stat computation to the shared `features/` modules, so that the walk-forward evaluation uses identical feature definitions to the batch pipeline.
10. As a developer, I want `predict.py` to merge trainer statistics onto today's race cards, so that trainer features are available at prediction time.
11. As a developer, I want `Trainer_Stats.csv` to be produced by `build_features` alongside `Horse_Stats.csv` and `Jockey_Stats.csv`, so that trainer features are available without re-running the full historical pipeline.
12. As a data scientist, I want `Last3RaceAvgSpeed`, `Last3RaceSpeedTrend`, and `Last3AvgRelFinishingPosition` included in the model's predictor set, so that multi-race trends are used when training and predicting.
13. As a data scientist, I want trainer win percentage, top-3 percentage, average relative finishing position, and number of prior races included in the model's predictor set, so that trainer quality is factored into predictions.
14. As a data scientist, I want notebooks to remain available for interactive exploration and visualisation, so that I can inspect feature distributions and diagnose model behaviour without running the full pipeline from scratch.
15. As a data scientist, I want notebooks to call `FeaturePipeline` for load/process/save rather than reimplementing the logic themselves, so that exploratory analysis always reflects production feature definitions.
16. As a developer, I want comprehensive unit tests for all modules in `race_analytics/features/`, so that regressions in feature computation are caught before they affect model results.
17. As a developer, I want existing tests refactored to use the new import paths, so that the test suite stays green after the move.
18. As a developer, I want the `tests/` directory structure to mirror the `race_analytics/features/` structure, so that it is easy to find the tests for a given module.
19. As a developer, I want `run.ps1` updated to call `build_features` once instead of converting and running three notebooks, so that the production pipeline is simpler and faster.
20. As a developer, I want `loader.py` to provide utilities for loading historical results CSVs, today's race cards, and pre-built stats files, so that notebooks, scripts, and tests all load data the same way.

## Implementation Decisions

- A new `race_analytics/features/` package is created as the single home for all feature engineering code.
- `features/transforms.py` absorbs the content of `utils/data_transforms.py`: surface, going, and race-type one-hot encoding; speed calculation; weight cleaning; horse count calculation; weight-change and distance-change calculation.
- `features/horse_stats.py` absorbs the `CalculateHorsesStats` class from `utils/data_analysis.py`, preserving its stateful incremental interface.
- `features/jockey_stats.py` absorbs the `CalculateJockeyStats` class from `utils/data_analysis.py`.
- `features/trainer_stats.py` absorbs the `CalculateTrainerStats` class from `utils/data_analysis.py`.
- `features/race_filters.py` absorbs the `CalculateRacesWithKnownHorsesAndJockeys` class from `utils/data_analysis.py`.
- `features/loader.py` provides data loading utilities: loading historical results CSVs sorted chronologically, loading today's race cards, and loading pre-built stats files (`Race_Features.csv`, `Horse_Stats.csv`, `Jockey_Stats.csv`, `Trainer_Stats.csv`).
- `features/pipeline.py` contains a stateful `FeaturePipeline` class that orchestrates the modules above. It accepts data in chronological order (the caller — normally the loader — is responsible for ordering). It exposes a `process(df)` method that returns an enriched DataFrame and accumulates internal state across calls. It also exposes save methods for each output CSV.
- `utils/data_transforms.py` and `utils/data_analysis.py` are deleted with no re-export shims. All callers are updated to import from `features/`.
- `utils/scoring.py` and `utils/data_path.py` remain in `utils/` as genuinely cross-cutting utilities.
- A new `race_analytics/scripts/build_features.py` script is added. It uses `loader.py` to load historical results in chronological order, runs `FeaturePipeline.process()`, and saves `Race_Features.csv`, `Horse_Stats.csv`, `Jockey_Stats.csv`, and `Trainer_Stats.csv`.
- `run.ps1` is updated to replace the three `nbconvert` + run blocks with a single call to `build_features`.
- `evaluate.py` removes its private `_compute_horse_stats()` and `_compute_jockey_stats()` methods and delegates to `features/horse_stats.py` and `features/jockey_stats.py` instead.
- `predict.py` is updated to load and merge `Trainer_Stats.csv` alongside `Horse_Stats.csv` and `Jockey_Stats.csv`.
- The `PREDICTORS` list in `algorithms/base.py` is extended with: `Last3RaceAvgSpeed`, `Last3RaceSpeedTrend`, `Last3AvgRelFinishingPosition`, `TrainerNumberOfPriorRaces`, `TrainerWinPercentage`, `TrainerTop3Percentage`, `TrainerAvgRelFinishingPosition`.
- The `FeatureAnalysis`, `HorseStatsBuilder`, and `JockeyStatsBuilder` notebooks are simplified to use `FeaturePipeline` and `loader.py` for load/process/save, retaining their value for interactive visualisation. The `.py` nbconvert outputs remain gitignored.
- The `HorseStatsBuilder` and `JockeyStatsBuilder` notebooks no longer re-implement rolling-average or percentage logic — they delegate entirely to the shared modules.

## Testing Decisions

- Good tests verify external behaviour, not implementation details. For the `features/` modules this means: given a DataFrame with known input rows in chronological order, assert on the output columns produced — not on internal state or intermediate variables.
- `features/transforms.py` contains pure functions and should be comprehensively unit tested: every encoding variant (all-weather, dirt, turf; all going categories; all race types), edge cases (unknown going string, zero distance, invalid speed), and NaN propagation.
- `features/horse_stats.py`, `features/jockey_stats.py`, and `features/trainer_stats.py` contain stateful classes. Tests should construct minimal DataFrames in chronological order and assert that the output columns are correct after one or more calls to `process()`.
- `features/race_filters.py` should be tested by constructing races with known horse/jockey history and asserting the filter flags are set correctly.
- `features/pipeline.py` should have an end-to-end smoke test: given a small synthetic dataset in chronological order, assert that the output DataFrame contains the expected columns and that the saved CSV files are produced.
- `features/loader.py` should be tested using a temporary directory with fixture CSV files.
- Existing tests in `tests/` are refactored to use the new import paths from `features/` and to remove any imports from the deleted `utils/data_transforms.py` and `utils/data_analysis.py`.
- The Python side of this project currently has limited test coverage; this PRD treats comprehensive pytest-style unit testing of all new `features/` modules as a core deliverable, not an optional add-on.
- Tests live in `tests/` mirroring the `race_analytics/features/` package structure (e.g. `tests/features/test_transforms.py`, `tests/features/test_horse_stats.py`).

## Out of Scope

- Changes to the C# extraction stage (`RaceDataDownloader`, `RacePredictor.Core`).
- Changes to the CSV schema of the raw `Results_YYYYMM.csv` files.
- Changes to the prediction algorithm implementations themselves (Ridge, XGBoost, ProxyTSR, etc.) beyond updating the `PREDICTORS` list.
- Hyperparameter tuning or model re-evaluation following the addition of new features to `PREDICTORS`.
- Adding new features beyond those already computed but unused (`Last3Race*`, `TrainerStats`).
- Removing the notebooks from the repository.
- CI/CD or GitHub Actions changes.

## Further Notes

- The walk-forward evaluation in `evaluate.py` processes data one day at a time and must continue to work correctly after the refactor. The `FeaturePipeline`'s stateful design (accumulating horse/jockey/trainer history across calls) is what makes this possible with a single interface.
- The addition of trainer features to `PREDICTORS` will change model outputs. Evaluation metrics should be re-run after the refactor to verify the impact.
- The `Last3Race*` features are only defined for horses with three or more prior races. The pipeline must continue to produce NaN for horses with fewer prior races, and the algorithms must handle NaN predictors (as they currently do via their existing imputation or NaN-handling logic).
- Chronological ordering is the caller's responsibility. `loader.py` enforces this when loading from disk; tests are responsible for constructing DataFrames in the correct order.
