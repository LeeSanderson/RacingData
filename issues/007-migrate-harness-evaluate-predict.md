# 007 — Migrate the harness (`evaluate.py` + `predict.py`) to `RaceData` + the Protocol contract

**Type:** AFK
**Parent RFC:** `issues/001-unify-prediction-data-path-racedata.md`
**Status:** Proposed
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

- [ ] `evaluate.py` builds `RaceData` once per fold; no `hasattr`/`getattr`/`type(a)(...)` probing of algorithms.
- [ ] `predict.py` produces a byte-identical `TodaysPredictions.csv` to the current implementation on a fixed
      fixture (the active algorithm's picks are unchanged).
- [ ] `evaluate.py` summary metrics on a fixed small fold set are unchanged vs the pre-migration run
      (accuracy/ROI/coverage) — guards against silent drift.
- [ ] `tests/scripts/test_evaluate.py`, `test_predict.py` pass.
- [ ] `python -m pytest tests/` green.

## Tests

Pin `predict.py` output and a 2-fold `evaluate.py` summary on a fixture before migrating, then assert equality
after. Add a contract test: the harness consumes a fake `FieldPredictor` with no reflective attribute checks.

## Notes

- This is the slice most exposed to silent metric drift — keep the before/after equality gates strict.
