# 003 — Deepen `FieldPredictorBaseAlgorithm` into the `RaceData` template engine

**Type:** AFK
**Parent RFC:** `issues/001-unify-prediction-data-path-racedata.md`
**Status:** Done (2026-06-13) — engine added to `race_analytics/algorithms/base.py` + `tests/algorithms/test_field_predictor_engine.py`
**Blocked by:** `issues/002-racedata-value-object-and-builder.md`

RFC migration step 2. Introduce the convention-driven template that owns the shared data-path,
operating on `RaceData`. Existing four-frame algorithms keep working unchanged (via the `from_legacy`
adapter) so the suite stays green; they are migrated one at a time in 004/005.

## What to build

In `race_analytics/algorithms/base.py`:

- A declared `FieldPredictor` `Protocol` (`runtime_checkable`): `max_horses`, `fit(data: RaceData)`,
  `predict_field(data: RaceData)`, `predict(data: RaceData)`. Plus an `AbstainCapable` Protocol
  (`predict_field_unfiltered`, `get_confidence_gate`/`confidence_gate`).
- The engine on `FieldPredictorBaseAlgorithm`:
  - **Convention knobs** (class-level): `label_col` (`"Wins"`), `score_col` (`"WinProbability"`),
    `return_full_field` (`True`), `nan_tolerant_predictors`, `extra_nan_tolerant_features`.
  - **Hooks** with identity/None defaults: `_prepare_training(data)`, `_prepare_serving(data)`,
    `_race_gate(data)`, `_sample_weight(frame)`; abstract `_fit_estimator(X, frame, sample_weight)` and
    `_score(X)`.
  - **Concrete shared data-path:** `fit(data)` (prepare → select features → dropna-required → fit) and
    `predict_field(data)` (prepare-serving → dropna-required → `_keep_complete_races`
    [`OriginalCount == PredictableCount <= max_horses`] → `_race_gate` → score → `_rank_within_race`),
    `predict(data)` = top-1. Helpers `_select_features` / `_dropna_required` / `_keep_complete_races` /
    `_rank_within_race` / `_top1` / `_empty` implemented once on the base.

## Acceptance criteria

- [x] `FieldPredictor` + `AbstainCapable` Protocols defined; `FieldPredictorBaseAlgorithm` exposes the
      `RaceData`-based `fit`/`predict_field`/`predict` template with the knobs and hooks above.
- [x] A transitional adapter keeps the existing four-frame algorithms passing **unchanged** (type dispatch:
      a `RaceData` runs the engine, the four-frame signature flows to subclass overrides). No subclass migrated.
- [x] New engine-boundary tests pass using a **fake estimator** (`fit`/`predict_proba`/`predict`) over a
      hand-built `RaceData`: `predict_field` returns the full scored field with `score_col` + `PredictedRank`;
      `predict` returns top-1; the complete-race/max-field filter drops the right races; a `_race_gate` override
      drops the right races pre-score.
- [x] `python -m pytest tests/` green (406 passed).

## Tests

New `tests/algorithms/test_field_predictor_engine.py` (fake estimator + `RaceData` fixture from 002).

## Notes

- The exact transitional mechanism (avoiding a `fit` signature collision between the new `RaceData` API and
  the legacy four-frame API) is an implementation choice — pick whatever keeps the existing suite green; it is
  torn down in issue 008.
- No behavior change to any production prediction in this slice.
