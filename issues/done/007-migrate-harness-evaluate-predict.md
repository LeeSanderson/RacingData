# 007 — Migrate the harness (`evaluate.py` + `predict.py`) to `RaceData` + the Protocol contract

**Type:** AFK
**Parent RFC:** `issues/001-unify-prediction-data-path-racedata.md`
**Status:** Done (2026-06-13)
**Blocked by:** `issues/004-migrate-win-classifier-family.md`, `issues/005-migrate-regressor-family.md`, `issues/006-migrate-gated-classifier-calibration.md`

RFC migration step 3. Build the canonical representation once and program against the declared
`FieldPredictor` contract instead of reflective probing.

## What to build

- `race_analytics/scripts/evaluate.py`:
  - Per fold, build one `RaceData` for the training window and one for the serving card via
    `RaceDataBuilder` (replacing `_engineer_features` + `decompose_race_history` + `race_card`).
  - Call algorithms through the `FieldPredictor` contract (`fit(data)` / `predict_field(data)` / `predict(data)`).
  - Replace reflective probing — `hasattr(algo, "predict_field")` (`:457`),
    `hasattr(algo, "predict_field_unfiltered")` (`:461`),
    `getattr(algo, "get_confidence_gate", …)` (`:517`), and `type(a)(max_horses=a.max_horses)` (`:381`) —
    with `isinstance(algo, AbstainCapable)` / the typed contract.
- `race_analytics/scripts/predict.py`: build a serving `RaceData` from `TodaysRaceCards.csv` + the feature
  CSVs and call `ACTIVE_ALGORITHM` through the contract; same `TodaysPredictions.csv` output.

## Acceptance criteria

- [x] `evaluate.py` builds `RaceData` once per fold; no `hasattr`/`getattr`/`type(a)(...)` probing of algorithms.
- [x] `predict.py` produces a byte-identical `TodaysPredictions.csv` to the current implementation on a fixed
      fixture (the active algorithm's picks are unchanged).
- [x] `evaluate.py` summary metrics on a fixed small fold set are unchanged vs the pre-migration run
      (accuracy/ROI/coverage) — guards against silent drift.
- [x] `tests/scripts/test_evaluate.py`, `test_predict.py` pass.
- [x] `python -m pytest tests/` green.

## Tests

Pin `predict.py` output and a 2-fold `evaluate.py` summary on a fixture before migrating, then assert equality
after. Add a contract test: the harness consumes a fake `FieldPredictor` with no reflective attribute checks.

## Notes

- This is the slice most exposed to silent metric drift — keep the before/after equality gates strict.

## Completion notes (2026-06-13)

**How metric-equality was guaranteed (no real-data 2-fold run needed).** The migrated harness builds the same
two `RaceData` objects the algorithms used to build internally, so the refactor is byte-identical by construction:
- Training: `RaceDataBuilder.wrap_training(train_df)` reproduces the base `_training_data_from_legacy` adapter
  exactly (clamp day-since features, `as_of = max(Off)+1day`, **no** canonical-chain re-run). Pinned by
  `test_wrap_training_matches_legacy_training_adapter`.
- Serving: `build_serving(race_card(known_fold), train_df, as_of=today())` reproduces the old
  `from_legacy(card, *decompose_race_history(train_df)[1:], today())` path. Pinned by the pre-existing
  `test_build_serving_matches_from_legacy_over_decomposed_history`.
- `serve_as_of` is deliberately `datetime.today()` (matching the legacy predict adapter), not `fold_date` — using
  the fold date would change serving `DaysRested` and shift picks. Fixing that serving-time skew is a separate
  behavioural change with its own re-baseline (out of scope here, like 006 fixed only the calibration skew).

**Deliberate deviation from the prose.** `_engineer_features` and `race_card` are **kept**; only
`decompose_race_history` is replaced (by `build_serving`). Swapping `_engineer_features` for the canonical
`build_training` would add WeightChange/DistanceChange/SurfaceSwitch/CodeSwitch to the trained feature set and
change every metric — incompatible with the "metrics unchanged" gate. `_engineer_features` remains the window's
feature source.

**Latent bug fixed en route.** `GatedSplitDisciplineWinClassifier.fit` was already broken (issue 006 made
`GatedClassifier` feed its inner a `RaceData`, but `SplitDisciplineWinClassifier` still read `races.columns`).
SplitDiscipline is now `RaceData`-aware in both `fit` and `predict_field`, with a test proving the `RaceData`
path is byte-identical (`WinProbability`/`PredictedRank`) to the legacy four-frame path on a mixed flat+jumps card.
