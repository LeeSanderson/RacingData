# 005 — Migrate the regressor family onto the engine

**Type:** AFK
**Parent RFC:** `issues/001-unify-prediction-data-path-racedata.md`
**Status:** Proposed
**Blocked by:** `issues/003-deepen-fieldpredictor-engine.md`

RFC migration step 2 (continued). Move `RegressorAlgorithm` and its subclasses onto the engine by
flipping conventions; delete the second copy of the predict data-path.

## What to build

- `regressor.py` — `RegressorAlgorithm` becomes an engine subclass: `label_col = "Speed"`,
  `score_col = "PredictedSpeed"`, `return_full_field = False` (top-1), implementing `_fit_estimator`
  (`model.fit(X, frame["Speed"])`) and `_score` (`model.predict(X)`). Delete its `predict(...)` body
  (the merge/clamp/encode/complete-race/rank pipeline) — now owned by `RaceDataBuilder` + the base.
- `ridge_regression.py`, `xgboost_algorithm.py` — keep their `_create_model()`; no pipeline code.
- Reconcile the regressor's encode-order nuances (`calculate_horse_count` conditional,
  `calculate_draw_features` last, no `encode_headgear`) against the canonical builder order, pinned by a
  characterization test before the cut-over (see RFC "silent metric drift is expensive").

## Acceptance criteria

- [ ] Regressor algorithms run through the base engine template with no bespoke pipeline code.
- [ ] Characterization: the regressor's top-1 output on a fixed fixture is identical before and after the
      migration (pin the legacy `predict(...)` output first, then assert equality).
- [ ] `tests/algorithms/test_ridge_regression.py`, `test_xgboost_algorithm.py`,
      `test_regressor_two_tier_dropna.py` pass (migrated to the `RaceData` signature).
- [ ] `python -m pytest tests/` green.

## Tests

Add a regressor characterization test capturing today's top-1 picks on the shared fixture; fold the
two-tier dropna assertions into the engine-boundary tests.

## Notes

- If the canonical (classifier) order and the regressor order produce *different* features for any row, that
  divergence must be surfaced and resolved deliberately here — it is exactly the kind of silent train/predict
  skew the RFC is removing.
