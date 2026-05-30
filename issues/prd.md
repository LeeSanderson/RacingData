# PRD: Evaluation Script — Timing Instrumentation & Prediction CSV Export

## Problem Statement

The evaluation script (`evaluate.py`) runs a walk-forward fold loop over multiple algorithms but provides no insight into how long each algorithm takes to fit or predict. When comparing algorithms, cost matters as much as accuracy — a marginally better model that takes 10× longer to train may not be worth using in production.

Additionally, the only output from an evaluation run is printed console text. There is no machine-readable record of which predictions each algorithm made, whether they were correct, or what race context surrounded them. This makes it impossible to do post-hoc analysis to identify patterns — e.g. "which surfaces does XGBoost get wrong?", "does accuracy degrade for long distances?" — that would guide future improvements.

## Solution

Extend the evaluation script with two capabilities:

1. **Timing instrumentation**: Capture separate fit and predict times (in seconds) for each algorithm on each fold. Display them inline on the per-fold output line and in a dedicated timing summary table showing mean and standard deviation across folds.

2. **Prediction CSV export**: Optionally write a CSV file containing one row per algorithm per race prediction, including race metadata, the predicted horse, the actual finishing position, odds, and raw model score where available. This file becomes the primary input for downstream strategy analysis.

## User Stories

1. As a data scientist running evaluations, I want to see fit and predict times appended to each fold's output line, so that I can spot which algorithms are slow without leaving the console.
2. As a data scientist running evaluations, I want fit and predict times displayed separately, so that I can distinguish training cost from inference cost.
3. As a data scientist running evaluations, I want times displayed in seconds to three decimal places, so that I can compare algorithms on a consistent, readable scale.
4. As a data scientist reviewing a completed evaluation run, I want a second summary table showing mean and standard deviation of fit and predict times per algorithm, so that I can assess both typical cost and consistency across folds.
5. As a data scientist, I want the timing summary printed after the existing accuracy/ROI summary table, so that the primary metrics remain visually prominent.
6. As a data scientist, I want to pass `--save-results` to the evaluation script to enable CSV output, so that I have an explicit opt-in that does not produce files by default.
7. As a data scientist, I want to pass `--results-file PATH` to specify where the CSV is written, so that I can control output location in scripts and pipelines.
8. As a data scientist, I want `--results-file PATH` without `--save-results` to implicitly enable CSV saving, so that specifying a path is sufficient and I am not forced to pass redundant flags.
9. As a data scientist, I want the CSV to default to `evaluation_results_YYYYMMDD.csv` in the current working directory when no path is specified, so that output files are naturally dated and do not overwrite each other across runs.
10. As a data scientist, I want each row of the CSV to represent a single algorithm's top-1 prediction for a single race, so that the file maps cleanly to the accuracy metric and is easy to filter and group.
11. As a data scientist, I want the CSV to include `FoldDate`, `Algorithm`, `RaceId`, `HorseId`, `CourseName`, `Surface`, `Going`, `RaceType`, `DistanceInMeters`, `FinishingPosition`, `DecimalOdds`, and `PredictedScore`, so that I have everything needed to stratify results by race conditions.
12. As a data scientist, I want `Surface`, `Going`, and `RaceType` stored as raw string values (e.g. `Turf`, `Good`, `Flat`) rather than one-hot encoded columns, so that the CSV is human-readable and easy to group by in analysis tools.
13. As a data scientist, I want `PredictedScore` to be populated for algorithms that produce a numeric model score (e.g. `PredictedSpeed` from XGBoost-family), so that I can analyse calibration and confidence thresholds.
14. As a data scientist, I want `PredictedScore` to be null/empty for algorithms that do not produce a score (e.g. `MarketFavouriteBaseline`), so that the schema is uniform and the column is self-documenting about algorithm capability.
15. As a data scientist, I want `FinishingPosition` recorded (not just a boolean `Correct` flag), so that I can analyse near-misses (2nd, 3rd place) as well as outright wins.
16. As a data scientist, I want the CSV rows assembled incrementally inside the fold loop while `known_fold` metadata is in scope, so that raw string values for `Surface`, `Going`, `RaceType`, and `CourseName` are captured without a secondary join pass.
17. As a data scientist, I want the CSV written once at the end of the evaluation run rather than appended fold-by-fold, so that a partial run does not produce a misleading incomplete file.
18. As a developer writing tests, I want the timing accumulation and CSV assembly logic extracted into pure helper functions, so that they can be unit-tested in isolation without running the full fold pipeline.

## Implementation Decisions

- **Timing capture**: Use `time.perf_counter()` to bracket each `algo.fit()` and `algo.predict()` call independently. Store results in two new per-algorithm accumulators alongside the existing `all_preds` / `all_results_store` / `all_fav_preds` dicts: `all_fit_times` (list of floats, seconds) and `all_predict_times` (list of floats, seconds).

- **Per-fold line format**: Timing is appended at the end of the existing fold output line using the pipe separator already in use: `| fit=X.XXXs, predict=X.XXXs`.

- **Timing summary table**: A second table printed immediately after the accuracy/ROI summary. Columns: `Algorithm`, `Fit(avg)`, `Fit(std)`, `Pred(avg)`, `Pred(std)`, all in seconds to 3 decimal places. Computed from the accumulated time lists using `numpy.mean` and `numpy.std`.

- **New CLI flags**: `--save-results` (boolean store-true flag) and `--results-file PATH` (optional string). The `evaluate()` function signature gains corresponding `save_results: bool = False` and `results_file: str | None = None` parameters. If `results_file` is provided but `save_results` is not set, saving is implicitly enabled. Default filename: `evaluation_results_YYYYMMDD.csv` using today's date.

- **CSV row assembly**: Inside the per-algorithm loop, after `algo.predict()` returns `preds`, merge `preds` with `results_df` (on `RaceId`, `HorseId`) and with a metadata slice of `known_fold` (on `RaceId`, `HorseId`) to produce one row per predicted race. Append to a `csv_rows` list of DataFrames. At the end of all folds, concatenate and write via `pd.DataFrame.to_csv(index=False)`.

- **PredictedScore column**: Check whether `preds` contains a column named `PredictedSpeed` (the name used by `RegressorAlgorithm`). If present, rename to `PredictedScore` in the output row; if absent, set to `pd.NA`.

- **Raw metadata availability**: `known_fold` retains the original `Surface`, `Going`, `RaceType` string columns after `_engineer_features()` because the encode functions add new one-hot columns without dropping the originals. `CourseName` and `DistanceInMeters` are also present. No additional joins or pre-encoding snapshot needed.

- **evaluate() function signature change**: The `evaluate()` function gains `save_results` and `results_file` parameters. The `__main__` block parses the two new CLI flags and passes them through. No other callers exist in the codebase.

## Testing Decisions

- **Test location**: `tests/scripts/test_evaluate.py`, mirroring the `race_analytics/scripts/evaluate.py` package structure.

- **What makes a good test**: Test observable outputs — the timing values captured, the DataFrame schema written to CSV — not internal implementation details. Use lightweight stubs for algorithms and data rather than loading real CSV files.

- **Timing tests**: Extract a helper function (e.g. `_aggregate_times(times: list[float]) -> tuple[float, float]`) that returns `(mean, std)`. Unit-test it with known input lists. Separately, test that the fold loop correctly appends to `all_fit_times` and `all_predict_times` by running evaluate with a minimal fake algorithm and asserting the list lengths match the number of folds processed.

- **CSV tests**:
  - Test that `--save-results` (with no `--results-file`) produces a file named `evaluation_results_YYYYMMDD.csv` in the current directory with the correct column schema.
  - Test that `--results-file PATH` without `--save-results` also produces output at `PATH`.
  - Test that the `PredictedScore` column is populated from `PredictedSpeed` when present and is null when absent.
  - Test that `Surface`, `Going`, `RaceType` values in the CSV are raw strings, not one-hot-encoded integers.
  - Test that no CSV is written when neither flag is passed.

- **Prior art**: Existing tests in `tests/` use pandas DataFrames as fixtures. Follow the same pattern — construct minimal `train_df` / `fold_df` stubs rather than reading from `Data/`.

## Out of Scope

- Timing instrumentation for the `predict.py` (today's race card) script.
- Favourite baseline timing (MarketFavouriteBaseline is not fit/predict instrumented).
- CSV output for the favourite baseline predictions.
- Streaming/incremental CSV writes (partial-run recovery is not a goal).
- Any changes to algorithm implementations or the scoring utilities.
- Dashboard or visualisation of the results CSV — that is downstream analysis work.

## Further Notes

- The results CSV is intended as input to a separate strategy-analysis workflow. Column names should be stable and self-describing so that analysis notebooks do not need to be updated when new algorithms are added.
- The `PredictedScore` column name is intentionally generic (not `PredictedSpeed`) so that non-regressor algorithms can eventually populate it with a different kind of score without a schema change.
- The default filename uses today's date (the run date), not the fold date range, to avoid ambiguity when multiple runs cover overlapping fold windows.
