## Parent PRD

`issues/prd.md`

## What to build

Create `race_analytics/features/pipeline.py` containing a stateful `FeaturePipeline` class that orchestrates all feature engineering modules. This is the single entry point that both the `build_features` script and `evaluate.py` use. The caller (normally `loader.py`) is responsible for passing data in chronological order.

The class must expose:
- `process(df)` — applies transforms, updates internal state (horse/jockey/trainer/race-filter), returns the enriched DataFrame
- Save methods for each output: `save_race_features(path)`, `save_horse_stats(path)`, `save_jockey_stats(path)`, `save_trainer_stats(path)`

Write an end-to-end smoke test using a small synthetic dataset (no filesystem required for `process()`; save methods can use a temporary directory).

## Acceptance criteria

- [ ] `race_analytics/features/pipeline.py` exists with the `FeaturePipeline` class
- [ ] `race_analytics/features/__init__.py` exports `FeaturePipeline` and the loader functions
- [ ] `process(df)` returns a DataFrame containing all expected output columns (encoding columns, horse stats, jockey stats, trainer stats, race filter flags)
- [ ] State accumulates correctly across multiple calls to `process()` — a horse seen in call N is available as prior history in call N+1
- [ ] `tests/features/test_pipeline.py` exists with:
  - A smoke test: two batches of synthetic race data processed in order, output DataFrame contains expected columns
  - Save methods write correctly shaped CSV files to a temporary directory
- [ ] All existing tests pass

## Blocked by

- `issues/001-features-transforms.md`
- `issues/002-features-race-filters.md`
- `issues/003-features-horse-and-jockey-stats.md`
- `issues/004-features-trainer-stats.md`
- `issues/005-features-loader.md`

## User stories addressed

- User story 2 (identical results from notebooks and scripts)
- User story 6 (stateful pipeline works for batch and incremental use)
- User story 15 (notebooks call `FeaturePipeline` for load/process/save)
- User story 16 (comprehensive unit tests)
