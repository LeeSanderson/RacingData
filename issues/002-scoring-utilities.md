## Parent PRD

`issues/prd.md`

## What to build

Add `accuracy()` and `roi()` functions to `Data/utils/` so both `evaluate.py` and `predict.py` can share the same scoring logic. See the *Scoring* section of the parent PRD for the exact calculation definitions.

- **Accuracy**: percentage of predicted winners where `FinishingPosition == 1`.
- **ROI**: £1 stake per predicted race; winnings = `DecimalOdds × stake` for correct predictions; reported as percentage gain/loss.

## Acceptance criteria

- [ ] `Data/utils/scoring.py` (or equivalent location inside `Data/utils/`) exports `accuracy(predictions, results)` returning a float between 0 and 1
- [ ] `Data/utils/scoring.py` exports `roi(predictions, results)` returning a float representing percentage gain/loss (e.g. `0.12` for +12%)
- [ ] Both functions accept a predictions DataFrame (columns: `RaceId`, `HorseId`) and a results DataFrame (columns include `RaceId`, `HorseId`, `FinishingPosition`, `DecimalOdds`, `ResultStatus`)
- [ ] `Data/tests/test_scoring.py` covers: all predictions correct, all predictions wrong, a mixed case, and races with a non-standard `ResultStatus` (void / no result)
- [ ] Tests follow the existing pattern in `test_data_analysis.py` (small in-memory DataFrames, no file I/O)

## Blocked by

None — can start immediately.

## User stories addressed

- User story 6 (winner prediction accuracy as primary metric)
- User story 7 (ROI shown alongside accuracy as informational metric)
- User story 25 (data preparation logic separated from algorithm logic; scoring is a shared utility)
