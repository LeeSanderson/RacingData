# 004 — Migrate the win-classifier family onto the engine hooks

**Type:** AFK
**Parent RFC:** `issues/001-unify-prediction-data-path-racedata.md`
**Status:** Done (2026-06-13)
**Blocked by:** `issues/003-deepen-fieldpredictor-engine.md`

RFC migration step 2 (continued). Move the win-classifier family off the duplicated
`_run_prediction` body and onto the new `RaceData` engine hooks. Behavior-preserving.

## What to build

Reimplement these on the engine, supplying only what genuinely varies (`_prepare_training`,
`_prepare_serving`, `_fit_estimator`, `_score`, `_sample_weight`, `_race_gate`):

- `binary_win_classifier.py` — `BinaryWinClassifierAlgorithm` becomes a thin engine subclass; delete its
  copy of the merge/encode/dropna/rank pipeline (now owned by `RaceDataBuilder` + the base template).
- `win_classifier.py`, `tuned_win_classifier.py`, `position_weighted_win_classifier.py`,
  `split_discipline_win_classifier.py`, `ranking_classifier.py` — express each via hooks/knobs.
- `recency_weighted_win_classifier.py` — compute decay weights from `RaceData.as_of` (**fixes** the
  `datetime.today()` skew), exposed via `_sample_weight`.
- `ratings_xgboost.py` — `RatingsXGBoostAlgorithm` / `…Ungated`: the TSR completeness filter becomes a
  `_race_gate` override; `ProxyTSRModel` coupling moves into `_prepare_training`/`_prepare_serving`.

## Acceptance criteria

- [x] Every win-classifier algorithm runs through the base engine template; no algorithm contains its own
      merge/encode/complete-race/rank code.
- [x] `RecencyWeightedWinClassifier` weights derive from `RaceData.as_of`, verified by building two `RaceData`
      with different `as_of` and asserting different weights for identical rows.
- [x] Existing behavior preserved: `tests/algorithms/test_binary_win_classifier.py`,
      `test_recency_weighted_proxy_tsr.py`, `test_ratings_xgboost.py`, `test_predictors.py`,
      `test_last3_nan_tolerance.py`, `test_split_race_type.py`, `test_ltr_proxy_tsr.py` pass (migrated to the
      `RaceData` signature where they asserted on the four-frame API).
- [x] `python -m pytest tests/` green (409 passed).

## Completion notes (2026-06-13)

- The base `FieldPredictorBaseAlgorithm` now adapts the legacy calling shapes to `RaceData` (flat enriched
  frame for `fit` → clamp+wrap; four frames for `predict_field` → `RaceDataBuilder.from_legacy`) and runs the
  one engine path. Un-migrated callers (`evaluate.py`, `predict.py`, `GatedClassifier`,
  `SplitDisciplineWinClassifier`) keep working via these adapters until issues 006/007; they are deleted in 008.
- Each family member now supplies only what varies: `BinaryWinClassifier` (`_fit_estimator`/`_score` + the
  shared `_add_race_context` HorseCount/Rel hook), `WinClassifier` (proxy-TSR `_prepare_training`/`_prepare_serving`),
  `RatingsXGBoost(Ungated)` (`_race_gate`), `PositionWeighted` (`_sample_weight`), `RecencyWeighted`
  (`_sample_weight` from `as_of`), `RankingClassifier` (`label_col="FinishingPosition"` + ranker `_fit_estimator`/`_score`).
  `Tuned` and `SplitDiscipline` needed no change (hyperparams / orchestrator).
- **Behaviour-preserving incl. recency:** the adapter sets `as_of = max(Off).normalize() + 1 day` (the fold
  date), so the new `as_of`-based decay reproduces the legacy date arithmetic exactly — no metric drift. The
  fix is architectural (read `RaceData.as_of`, not `train_df["Off"]`), not numeric.
- `test_race_data.py`'s characterization now compares `from_legacy` against an inlined, frozen reference of the
  (deleted) `_run_prediction` merge+chain rather than patching production.
- Note for a future cleanup (out of scope): `race_analytics/scripts/fold_analysis.py` was already broken before
  this issue (imports `_compute_horse_stats`/`_race_card` from `evaluate.py` and `_add_race_context` from
  `ratings_xgboost`, none of which exist); left untouched.

## Tests

Fold the per-family merge/encode assertions into the engine-boundary test from 003 (parametrized over
weighting / estimator). Keep one behavior test per algorithm asserting its scoring/ranking output on the
shared fixture.

## Notes

- `_add_race_context` (the `Rel*` / `HorseCount` logic) moves into the canonical builder chain or a shared
  base helper — it must run identically for every family member.
