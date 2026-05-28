# Issue 004 — Migrate Ratings + Proxy classifiers to `BinaryWinClassifierAlgorithm` + Phase-A smoke eval

## Parent PRD

`issues/prd.md` — Phase A.

## What to build

Migrate the four concrete classifier algorithms onto the new
`BinaryWinClassifierAlgorithm` base introduced in issue 003, deleting the
duplicated ~150-line `fit` / `predict` bodies in `ratings_xgboost.py` and
`proxy_tsr_xgboost.py`. End the slice with a small-fold smoke evaluation
confirming Phase A is behaviour-preserving.

### Migrations

- `RatingsXGBoostAlgorithm` (`race_analytics/algorithms/ratings_xgboost.py`)
  - Inherits from `BinaryWinClassifierAlgorithm`.
  - `extra_nan_tolerant_features = RATING_COLS` (the three `LastRace*Rating`
    columns; their `Rel*` siblings are produced by the shared `_add_race_context`
    helper).
  - `_apply_gate` enforces the existing TSR-availability gate: keep only the
    races where every horse has a non-null `LastRaceTopSpeedRating`.
  - Delete the bespoke `fit` and `predict` overrides. Delete `_create_model`
    (vestigial) and the `require_tsr` constructor flag — the gate now lives in
    `_apply_gate`.
- `RatingsXGBoostUngatedAlgorithm` becomes a subclass of
  `RatingsXGBoostAlgorithm` that overrides `_apply_gate` to identity (returns
  `predictable` unchanged). No other differences.
- `ProxyTSRXGBoostAlgorithm`
  (`race_analytics/algorithms/proxy_tsr_xgboost.py`)
  - Inherits from `BinaryWinClassifierAlgorithm`.
  - `extra_nan_tolerant_features = RATING_COLS + ["LastProxyTSR"]`.
  - `_prepare_training_df` fits `self._proxy_model` on the fold-train slice,
    stores `self._horse_proxy_tsr = self._proxy_model.compute_horse_proxy_tsr(train_df)`,
    and returns `train_df` with `LastProxyTSR =
    self._proxy_model.compute_as_of_proxy(train_df)` attached.
  - `_prepare_prediction_df` merges `self._horse_proxy_tsr` onto the merged
    frame (left-join on `HorseId`).
  - No `_apply_gate` override (default identity — ProxyTSR is ungated by design).
  - Delete the bespoke `fit` and `predict` overrides. Delete `_create_model`
    (vestigial).
- `TunedProxyTSRXGBoostAlgorithm` keeps its tuned-hyperparameter
  constructor; it inherits the new `_prepare_*` hooks from
  `ProxyTSRXGBoostAlgorithm` without further changes.

### Smoke eval (end of slice)

After all unit tests are green, run a small-fold (~14-fold) evaluation against
the same data slice that produced the existing 415-race Phase-A baseline and
confirm per-algorithm race counts and accuracy reproduce within rounding. The
exact command (e.g. `python -m race_analytics.scripts.evaluate --folds 14 …`)
follows the existing convention in `race_analytics/scripts/evaluate.py`.
Capture the output as a brief note in the PR description (or commit message);
no checked-in artifact is required.

## Acceptance criteria

- [ ] Each of the four classifier classes inherits (directly or transitively)
      from `BinaryWinClassifierAlgorithm` and defines only `__init__` plus the
      hook overrides it needs.
- [ ] `ratings_xgboost.py` and `proxy_tsr_xgboost.py` no longer contain
      bespoke `fit` / `predict` bodies; the duplicated ~150-line blocks are
      deleted.
- [ ] `ALGORITHMS` and `ACTIVE_ALGORITHM` in
      `race_analytics/algorithms/__init__.py` are unchanged in shape;
      `ACTIVE_ALGORITHM` is still `ProxyTSRXGBoostAlgorithm`.
- [ ] Every test under `tests/race_analytics/algorithms/` passes unchanged.
- [ ] Small-fold smoke evaluation result is documented in the PR / commit
      message: per-algorithm race count and accuracy match the Phase-A
      baseline within rounding (≤1 race difference, ≤0.005 accuracy
      difference per algorithm).

## Blocked by

- Blocked by `issues/003-binary-win-classifier-middle-class.md`.

## User stories addressed

- User story 10
- User story 14
- User story 15
