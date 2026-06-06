## Parent PRD

`issues/prd.md`

## What to build

Add `SplitRaceTypeAlgorithm` in a new file `race_analytics/algorithms/split_race_type.py`. This algorithm trains separate `ProxyTSRXGBoostAlgorithm` instances for flat races (`RaceType_Flat == 1`) and jump races, routing each prediction to the appropriate sub-model.

Key implementation points:

- Holds `_flat_model` and `_jumps_model` (both `ProxyTSRXGBoostAlgorithm` instances) plus a `_fallback_model` trained on all data.
- `fit()`: split training data by race type; fit each sub-model if it has ≥ 100 training races, otherwise mark as unavailable and fit the fallback on all data.
- `predict()` / `predict_field()`: route each race to the appropriate sub-model; use fallback if the race type's sub-model is unavailable. Merge outputs before returning.
- `AbstainWrapperSplitAlgorithm` wraps `SplitRaceTypeAlgorithm`.
- Register both in `__init__.py` `ALGORITHMS` list.

See PRD §SplitRaceTypeAlgorithm for full spec.

## Acceptance criteria

- [ ] `split_race_type.py` exists containing `SplitRaceTypeAlgorithm` and `AbstainWrapperSplitAlgorithm`.
- [ ] Both are present in the `ALGORITHMS` list in `__init__.py`.
- [ ] Test in `tests/algorithms/test_split_race_type.py`: flat race predictions are routed to `_flat_model` and jump race predictions to `_jumps_model`.
- [ ] Test: when a race type has fewer than 100 training rows, the fallback model is used instead and no prediction is dropped.
- [ ] `pytest` full suite passes.

## Blocked by

- Blocked by `issues/011-headgear-features.md`

## User stories addressed

- User story 9
- User story 10
- User story 12
