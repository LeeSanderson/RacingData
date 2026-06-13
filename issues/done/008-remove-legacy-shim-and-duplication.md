# 008 — Remove the `from_legacy` shim and the duplicated four-frame predict paths

**Type:** AFK
**Parent RFC:** `issues/001-unify-prediction-data-path-racedata.md`
**Status:** Done (2026-06-13)
**Blocked by:** `issues/007-migrate-harness-evaluate-predict.md`

RFC migration step 5 — final cleanup. Once every algorithm and the harness consume `RaceData`, delete the
transitional scaffolding and the now-dead duplicated code.

## What to build (delete)

- `RaceDataBuilder.from_legacy(...)` and the transitional four-frame adapter added in issue 003.
- Any remaining four-frame `predict(...)` / `predict_field(...)` signatures on `base.py` and subclasses.
- The duplicated pipeline bodies that are now unreachable (the old `_run_prediction` in
  `binary_win_classifier.py`, the old `predict` in `regressor.py`).
- `decompose_race_history` in `features/race_history.py` if it has no remaining callers (and `race_card`
  if likewise unused).

## Acceptance criteria

- [x] No `from_legacy` references remain; the four-frame `(races, horse_stats, jockey_stats, trainer_stats)`
      signature is gone from the algorithm contract.
- [x] `grep` confirms `decompose_race_history` has zero callers (deleted from `features/race_history.py`).
- [x] The merge/encode/complete-race/rank pipeline exists in exactly one place (`RaceDataBuilder` + the base
      engine template).
- [x] `python -m pytest tests/` green (420 passed); `tests/features/test_race_history.py` trimmed to the
      `race_card` tests.

## Tests

Remove tests that only exercised the deleted shim / four-frame signature; ensure no coverage of live behavior
is lost (the behavior now lives behind the engine-boundary and builder characterization tests).

## Notes

- Out of scope (separate RFC candidates, per 001): centralizing scattered hyperparameters, replacing the
  index-based `ACTIVE_ALGORITHM` registry, and collapsing the thin weighting/objective subclasses into
  composable strategy objects.

## Completion notes (2026-06-13)

**`from_legacy` renamed, not deleted — the merge logic is canonical, not legacy.** The four-frame *algorithm
adapter* was the migration scaffolding; the card-plus-precomputed-stats *builder* is core (predict.py still
needs it: `FeaturePipeline.save_horse_stats` writes `extract_horse_stats(Race_Features)`, so the stats CSVs are
exactly what `build_serving` would extract). So `RaceDataBuilder.from_legacy` → `build_serving_from_stats`
(the single merge+chain path; `build_serving` extracts stats then delegates to it). predict.py calls it directly.

**Removed:** the `if not isinstance(data, RaceData)` adapter branches and `_training_data_from_legacy` from
`FieldPredictorBaseAlgorithm.fit/predict_field/predict` (now RaceData-only); `BaseAlgorithm`'s abstract
four-frame `predict` signature; `GatedClassifier`'s dual-shape `fit`/`predict_field`/`predict_field_unfiltered`
(+ `_inner_field`/`_race_frame`); `SplitDisciplineWinClassifier`'s legacy `fit`/`predict_field` branches (+
`_split_train_by_race_type`); and `decompose_race_history` (zero callers — only tests). `race_card` is kept
(used by evaluate.py/predict.py/analysis.py). `wrap_training` (the training-frame wrap) stays on the builder.

**Test migration.** Every algorithm test that drove `fit(flat_df)` + `predict(four frames)` now builds a
`RaceData` via local `_rd`/`_serve` helpers (`wrap_training` / `build_serving_from_stats`) and calls the
single-argument contract. Tests that only existed to prove the now-deleted scaffolding were removed (their live
behaviour is covered elsewhere): `test_fit_does_not_call_decompose_race_history` + the
`base.datetime`-patching `test_calibration_is_independent_of_wall_clock` (as_of→calibration is still pinned by
`test_different_as_of_calibrates_differently`); the SplitDiscipline legacy-vs-RaceData equivalence test (the
legacy path is gone — replaced by `test_mixed_card_routes_flat_and_jumps_through_the_split`);
`test_wrap_training_matches_legacy_training_adapter` (the adapter it compared against is deleted);
`decompose_race_history` unit tests in `test_race_history.py`.

This completes RFC 001: the prediction data-path is unified on `RaceData` with no remaining shim.
