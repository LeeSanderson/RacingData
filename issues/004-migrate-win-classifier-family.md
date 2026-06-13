# 004 — Migrate the win-classifier family onto the engine hooks

**Type:** AFK
**Parent RFC:** `issues/001-unify-prediction-data-path-racedata.md`
**Status:** Proposed
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

- [ ] Every win-classifier algorithm runs through the base engine template; no algorithm contains its own
      merge/encode/complete-race/rank code.
- [ ] `RecencyWeightedWinClassifier` weights derive from `RaceData.as_of`, verified by building two `RaceData`
      with different `as_of` and asserting different weights for identical rows.
- [ ] Existing behavior preserved: `tests/algorithms/test_binary_win_classifier.py`,
      `test_recency_weighted_proxy_tsr.py`, `test_ratings_xgboost.py`, `test_predictors.py`,
      `test_last3_nan_tolerance.py`, `test_split_race_type.py`, `test_ltr_proxy_tsr.py` pass (migrated to the
      `RaceData` signature where they asserted on the four-frame API).
- [ ] `python -m pytest tests/` green.

## Tests

Fold the per-family merge/encode assertions into the engine-boundary test from 003 (parametrized over
weighting / estimator). Keep one behavior test per algorithm asserting its scoring/ranking output on the
shared fixture.

## Notes

- `_add_race_context` (the `Rel*` / `HorseCount` logic) moves into the canonical builder chain or a shared
  base helper — it must run identically for every family member.
