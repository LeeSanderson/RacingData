# 005 — Migrate the regressor family onto the engine

**Type:** AFK
**Parent RFC:** `issues/001-unify-prediction-data-path-racedata.md`
**Status:** Done (2026-06-13)
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

- [x] Regressor algorithms run through the base engine template with no bespoke pipeline code.
- [x] Characterization: the regressor's top-1 output on a fixed fixture is identical before and after the
      migration (pin the legacy `predict(...)` output first, then assert equality).
- [x] `tests/algorithms/test_ridge_regression.py`, `test_xgboost_algorithm.py`,
      `test_regressor_two_tier_dropna.py` pass (they exercise the public `fit`/`predict` API, which the base
      engine's legacy adapters still accept — no signature change needed).
- [x] `python -m pytest tests/` green (411 passed).

## Completion notes (2026-06-13)

- `RegressorAlgorithm` now subclasses `FieldPredictorBaseAlgorithm` with `label_col="Speed"`,
  `score_col="PredictedSpeed"`, `return_full_field=False`, and only `_create_model`/`_fit_estimator`/`_score`.
  Its bespoke `fit`/`predict` merge-clamp-encode-complete-race-rank pipeline is deleted. `ridge_regression.py`
  and `xgboost_algorithm.py` are unchanged (just `_create_model`).
- **Feature-selection divergence resolved:** the engine's default `_select_features` (REQUIRED+OPTIONAL+…)
  would have handed Ridge the optional predictors it must NOT use. `RegressorAlgorithm._select_features` is
  overridden to the regressor's two-tier rule — `required + (nan_tolerant_predictors ∩ frame)` — so Ridge stays
  optional-free and XGBoost keeps tolerating OPTIONAL NaNs. It also sets `_fitted_predictors` for compatibility.
- **Encode-order / headgear divergence resolved (deliberately):** the legacy regressor serving chain omitted
  `encode_headgear`, so in the real harness — where the training frame carries the 7 encoded headgear columns
  and they enter `_fitted_predictors` — legacy `predict` would `KeyError` selecting columns its serving frame
  never built. Routing serving through `RaceDataBuilder.from_legacy` (the full canonical chain) materialises
  those columns, fixing the latent crash. The remaining transforms are order-independent for the shared feature
  columns (draw still runs after HorseCount), so on the no-headgear fixtures top-1 output is byte-identical —
  pinned by `test_regressor_characterization.py` (written GREEN against the legacy code, still GREEN after).
- Two-tier dropna assertions kept in `test_regressor_two_tier_dropna.py` (regressor-specific — they validate the
  `_select_features` override, not generic engine mechanics) rather than folded into the generic engine-boundary
  test, which uses a classifier-shaped fake.

## Tests

Add a regressor characterization test capturing today's top-1 picks on the shared fixture; fold the
two-tier dropna assertions into the engine-boundary tests.

## Notes

- If the canonical (classifier) order and the regressor order produce *different* features for any row, that
  divergence must be surfaced and resolved deliberately here — it is exactly the kind of silent train/predict
  skew the RFC is removing.
