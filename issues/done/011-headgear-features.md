## Parent PRD

`issues/prd.md`

## What to build

Add HeadGear encoding as a set of always-present binary features: `IsFirstTimeHeadgear`, `HasBlinkers`, `HasCheekpieces`, `HasTongueTie`, `HasHood`, `HasVisor`, and `HeadGearChanged`. Null/absent `HeadGear` encodes as all-false (no headgear) — these flags are never NaN and do not go into `OPTIONAL_PREDICTORS`.

The slice covers:

- `race_analytics/features/transforms.py`: new `encode_headgear(df)` pure function. `IsFirstTimeHeadgear` = any `*1` suffix in the raw `HeadGear` code. Binary type flags parsed from the code string. Null input → all flags False.
- `race_analytics/features/horse_stats.py`: add `LastRaceHeadGear` column to `CalculateHorsesStats`, recording the raw headgear code from the horse's most recent **prior** race (computed from the historical slice, not the current row).
- `HeadGearChanged` = current `HeadGear` ≠ `LastRaceHeadGear` (False when both are null).
- `race_analytics/algorithms/base.py` (or `binary_win_classifier.py`): add all seven new columns to the **required** predictor list (not `OPTIONAL_PREDICTORS`).
- `race_analytics/algorithms/binary_win_classifier.py`: call `encode_headgear` in `_run_prediction` alongside `encode_surfaces`, `encode_going`, etc.
- `race_analytics/scripts/evaluate.py`: call `encode_headgear` in `_engineer_features`.
- Run `feature_screen.py` as a manual validation step: confirm non-zero XGBoost importance for at least some headgear flags and no odds-derived leakage introduced.

See PRD §HeadGear features for full encoding spec.

## Acceptance criteria

- [ ] `encode_headgear(df)` exists in `transforms.py` and returns all seven columns with correct values for `"b1"`, `"tp1"`, `None`, and multi-code combinations.
- [ ] `CalculateHorsesStats` produces a `LastRaceHeadGear` column reflecting the horse's most recent prior race (not the current row).
- [ ] `HeadGearChanged` is True when the current headgear code differs from `LastRaceHeadGear`, False when identical or both null.
- [ ] All seven headgear columns are included as required predictors (present in every training/prediction DataFrame, never NaN).
- [ ] `pytest tests/features/test_transforms.py` includes tests for `encode_headgear` covering: known codes, null input, multi-code input.
- [ ] `pytest tests/features/test_horse_stats.py` includes a test asserting `LastRaceHeadGear` reflects the prior race, not the current row.
- [ ] `pytest` full suite passes.
- [ ] Manual: `feature_screen.py` reports non-zero importance for at least one headgear flag.

## Blocked by

None — can start immediately.

## User stories addressed

- User story 1
- User story 2
- User story 3
- User story 4
