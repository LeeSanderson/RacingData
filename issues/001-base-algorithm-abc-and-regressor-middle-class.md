# Issue 001 — `BaseAlgorithm` ABC + `RegressorAlgorithm` middle class + migrate regressors

## Parent PRD

`issues/prd.md` — Phase A.

## What to build

Restructure `race_analytics/algorithms/base.py` so that `BaseAlgorithm` becomes a
pure abstract polymorphic interface and the existing Speed-target sklearn-style
regressor body moves down to a new concrete sibling `RegressorAlgorithm`.

- `BaseAlgorithm` becomes an `abc.ABC` declaring `fit(train_df)` and
  `predict(races, horse_stats, jockey_stats, trainer_stats=None)` as
  `@abstractmethod`. Its `__init__` keeps only `max_horses` (it no longer calls
  `self._create_model()` or seeds `self._fitted_predictors`).
- The current concrete `fit`/`predict` body in `BaseAlgorithm` (the Speed-target
  flow, the `dropna()` on `PREDICTORS`, the merge / encode / `DaysRested` cap
  helpers, and the `OriginalCount == PredictableCount && OriginalCount <= max_horses`
  filter) moves into a new `RegressorAlgorithm(BaseAlgorithm)` in
  `race_analytics/algorithms/regressor.py` (or in `base.py` if you prefer a
  single-file home — pick one and be consistent).
- `RegressorAlgorithm.__init__` takes `max_horses`, calls `super().__init__`,
  and sets `self._model = self._create_model()` and
  `self._fitted_predictors = list(PREDICTORS)`. `_create_model` stays
  `@abstractmethod` on `RegressorAlgorithm`.
- Migrate `RidgeRegressionAlgorithm` and `XGBoostAlgorithm` to inherit from
  `RegressorAlgorithm`. Their bodies stay one-method (`_create_model`) overrides.
- `RatingsXGBoostAlgorithm` and `ProxyTSRXGBoostAlgorithm` keep inheriting from
  `BaseAlgorithm` for now. Their existing `fit` / `predict` overrides satisfy
  the new abstract contract. Their `_create_model` methods become vestigial but
  do no harm (cleaned up in issue 004).
- `ALGORITHMS` and `ACTIVE_ALGORITHM` in `race_analytics/algorithms/__init__.py`
  keep their current shape; only the inheritance of the listed classes changes.

This slice is strictly behaviour-preserving: every existing unit test must pass
unchanged.

## Acceptance criteria

- [ ] `BaseAlgorithm` is an `abc.ABC` with `fit` and `predict` declared
      `@abstractmethod` and no concrete sklearn-pipeline body.
- [ ] A new `RegressorAlgorithm` class carries the previous Speed-target
      `fit`/`predict` body verbatim (modulo moving `self._model` /
      `self._fitted_predictors` setup into its `__init__`).
- [ ] `RidgeRegressionAlgorithm` and `XGBoostAlgorithm` inherit from
      `RegressorAlgorithm` and define only `_create_model`.
- [ ] `RatingsXGBoostAlgorithm` and `ProxyTSRXGBoostAlgorithm` instantiate
      without raising `TypeError: Can't instantiate abstract class …`.
- [ ] Every test under `tests/race_analytics/algorithms/` passes unchanged
      (`pytest tests/race_analytics/algorithms -q` is green).
- [ ] `from race_analytics.algorithms import ALGORITHMS, ACTIVE_ALGORITHM`
      still works; `ACTIVE_ALGORITHM` is still `ProxyTSRXGBoostAlgorithm`.

## Blocked by

None — can start immediately.

## User stories addressed

- User story 2
- User story 3
- User story 4
- User story 6
- User story 14
