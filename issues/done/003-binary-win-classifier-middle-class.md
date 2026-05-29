# Issue 003 — `BinaryWinClassifierAlgorithm` middle class with hooks

## Parent PRD

`issues/prd.md` — Phase A.

## What to build

Introduce the second middle class in the hierarchy:
`BinaryWinClassifierAlgorithm(BaseAlgorithm)`, which encodes the Wins-target
XGBClassifier flow currently duplicated across
`race_analytics/algorithms/ratings_xgboost.py` and
`race_analytics/algorithms/proxy_tsr_xgboost.py`. This slice **introduces** the
class and exercises it via focused tests; the migrations of the two concrete
classifiers happen in issue 004.

- Land the class in `race_analytics/algorithms/binary_win_classifier.py`
  (or in `base.py` — pick whichever matches issue 001's placement).
- Encapsulate the shared body:
  - `__init__` accepts the XGBClassifier (created by the subclass) and stores
    it alongside `max_horses`; calls `super().__init__(max_horses)`.
  - The shared `fit` body:
    1. `df = self._prepare_training_df(train_df)` (default identity)
    2. Apply `_add_race_context`-style rel-cols if the subclass uses any —
       reuse / hoist the existing helper from `ratings_xgboost.py` so both
       concrete classes can share it (define `extra_nan_tolerant_features`
       to drive which columns get `Rel*` siblings).
    3. Feature list = `REQUIRED_PREDICTORS + OPTIONAL_PREDICTORS +
       self.extra_nan_tolerant_features + ["HorseCount"]`, intersected with
       columns actually present.
    4. Required-for-dropna subset = `REQUIRED_PREDICTORS ∩ available` plus
       `"Wins"`. Tolerated subset = `OPTIONAL_PREDICTORS +
       self.extra_nan_tolerant_features`.
    5. Cap `DaysRested` / `DaysSinceJockeyLastRaced` at 10 (existing behaviour).
    6. `self._classifier.fit(data[available], data["Wins"])`.
  - The shared `predict` body:
    1. Same merge / encode pipeline as today.
    2. `merged = self._prepare_prediction_df(merged)` (default identity).
    3. `_add_race_context` (relative-rating columns).
    4. Two-tier dropna on the per-horse `predictable` frame using the same
       required / tolerated split.
    5. Standard `OriginalCount == PredictableCount && OriginalCount <= max_horses`
       gate (kept races where every horse has every required column).
    6. `predictable = self._apply_gate(predictable)` (default identity).
    7. `predict_proba(...)`, rank within race, return rank-1 per race.
- Hook contract (all defaults are identity / empty):
  - `extra_nan_tolerant_features: ClassVar[list[str]] = []`
  - `_prepare_training_df(self, train_df: pd.DataFrame) -> pd.DataFrame`
  - `_prepare_prediction_df(self, merged: pd.DataFrame) -> pd.DataFrame`
  - `_apply_gate(self, predictable: pd.DataFrame) -> pd.DataFrame`
- The class implements concrete `fit` / `predict`, satisfying
  `BaseAlgorithm`'s abstract contract. Subclasses do **not** override
  `fit`/`predict` — they override the hooks plus `_create_model` /
  `self._classifier`.

## Acceptance criteria

- [ ] `BinaryWinClassifierAlgorithm(BaseAlgorithm)` exists with concrete
      `fit` and `predict` and the four hooks above (defaults: identity / empty).
- [ ] No concrete algorithm in `ALGORITHMS` is migrated yet — the registry is
      unchanged and every existing unit test still passes.
- [ ] A new unit test instantiates a minimal `BinaryWinClassifierAlgorithm`
      subclass that overrides each hook with a spy and asserts:
      - `_prepare_training_df` is invoked exactly once during `fit`, on the
        full training frame, **before** dropna.
      - `_prepare_prediction_df` is invoked exactly once during `predict`,
        on the merged frame, **before** the `predictable` dropna.
      - `_apply_gate` is invoked exactly once during `predict`, on the
        post-`OriginalCount==PredictableCount` predictable frame, **before**
        scoring.
      - A column listed in `extra_nan_tolerant_features` is fed into the
        classifier even when some rows are NaN in that column, while a row
        with NaN in a `REQUIRED_PREDICTORS` column is dropped.
- [ ] `pytest tests/race_analytics/algorithms -q` is green.

## Blocked by

- Blocked by `issues/001-base-algorithm-abc-and-regressor-middle-class.md`.

## User stories addressed

- User story 5
- User story 8
- User story 9
- User story 14
