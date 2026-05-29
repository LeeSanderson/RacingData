# Issue 002 — `nan_tolerant_predictors` class attribute + two-tier dropna on `RegressorAlgorithm`

## Parent PRD

`issues/prd.md` — Phase A.

## What to build

Introduce the declarative opt-in mechanism the PRD's "Implementation Decisions"
section describes, and wire it into `RegressorAlgorithm.fit` as a two-tier
dropna. This slice stays behaviour-preserving because every algorithm defaults
to an empty `nan_tolerant_predictors` list — actual coverage changes land in
issue 005.

- In `race_analytics/algorithms/base.py`, split the existing `PREDICTORS`
  constant:
  - `REQUIRED_PREDICTORS` — every entry currently in `PREDICTORS` except the
    three `Last3*` columns (`Last3RaceAvgSpeed`, `Last3RaceSpeedTrend`,
    `Last3AvgRelFinishingPosition`).
  - `OPTIONAL_PREDICTORS` — those three `Last3*` columns.
  - Keep `PREDICTORS = REQUIRED_PREDICTORS + OPTIONAL_PREDICTORS` as a
    backward-compatibility alias.
- Add `BaseAlgorithm.nan_tolerant_predictors: ClassVar[list[str]] = []` as
  the declarative opt-in mechanism. Subclasses override.
- Rewrite `RegressorAlgorithm.fit` to apply two-tier dropna:
  - Required subset = `REQUIRED_PREDICTORS ∩ train_df.columns` plus `"Speed"`.
  - Tolerated subset = `self.nan_tolerant_predictors ∩ train_df.columns`.
  - `data = train_df[required + tolerated + ["Speed"]].dropna(subset=required)`
    (i.e. rows are dropped iff they are NaN in a required column).
  - `self._fitted_predictors` reflects the full available column set
    (required + tolerated) so `predict` lines up.
- Apply the same two-tier filter at the per-row predictability check in
  `RegressorAlgorithm.predict` so its `OriginalCount == PredictableCount` gate
  uses the required subset, not the full `PREDICTORS` list.
- `RidgeRegressionAlgorithm` and `XGBoostAlgorithm` keep
  `nan_tolerant_predictors = []` (default). Phase A behaviour is unchanged.

## Acceptance criteria

- [ ] `base.py` exposes `REQUIRED_PREDICTORS`, `OPTIONAL_PREDICTORS`, and
      `PREDICTORS = REQUIRED_PREDICTORS + OPTIONAL_PREDICTORS`.
- [ ] `BaseAlgorithm.nan_tolerant_predictors` exists as a `ClassVar[list[str]]`
      defaulting to `[]`.
- [ ] `RegressorAlgorithm.fit` and `RegressorAlgorithm.predict` use the
      two-tier subset; rows are dropped iff a required column is NaN.
- [ ] A new unit test under `tests/race_analytics/algorithms/` constructs a
      tiny `RegressorAlgorithm` subclass with `nan_tolerant_predictors =
      ["SomeCol"]` and asserts:
      - A row with NaN in `SomeCol` (but all required columns present) is
        kept and contributes to fitting (where the underlying estimator
        supports NaN — use XGBoost-backed regressor for the test).
      - A row with NaN in a `REQUIRED_PREDICTORS` column is dropped.
- [ ] Every other existing test under `tests/race_analytics/algorithms/`
      passes unchanged.

## Blocked by

- Blocked by `issues/001-base-algorithm-abc-and-regressor-middle-class.md`.

## User stories addressed

- User story 7
- User story 14
