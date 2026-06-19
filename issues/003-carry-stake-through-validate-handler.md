# Carry `Stake` through the C# `validate` handler to `PredictionScores`

## Parent PRD

`issues/prd.md` — "Modules built / modified" (forward-logging / validate command handler bullet), "Schema changes / contracts" (monthly prediction-scores CSV gains a trailing `Stake` column), "Testing Decisions".

## What to build

The forward-logging half. Add `[Optional] public double? Stake { get; set; }` to `RaceDataDownloader/Models/RaceCardPrediction.cs`; it is inherited by `RaceCardPredictionScore`. The `validate` command handler (`ValidateRaceCardPredictionsCommandHandler`) already reads `TodaysPredictions.csv` into `RaceCardPrediction` and writes the monthly `PredictionScores_YYYYMM.csv` from `RaceCardPredictionScore` — so once the property exists, the advised `Stake` rides from the prediction file through to each pick's recorded outcome with no further handler logic. CsvHelper's `[Optional]` keeps legacy prediction files (no `Stake` column) readable.

This is what makes an honest staked-ROI track record accrue from real forecast-priced days onward, and makes a calibration curve computable later.

## Acceptance criteria

- [ ] `RaceCardPrediction` has an `[Optional] double? Stake` property; `RaceCardPredictionScore` carries it through (inherited).
- [ ] Running `validate` over a `TodaysPredictions.csv` that contains a `Stake` column writes `PredictionScores_YYYYMM.csv` with a trailing `Stake` column whose value rides from input to output.
- [ ] A prediction file *without* a `Stake` column still loads (CsvHelper `[Optional]`), so older files don't break.
- [ ] `ValidateRaceCardPredictionsCommandHandlerShould` is extended with a test in the existing style — drive via `RunAsync`, deserialize the written CSV via `FromCsvString<RaceCardPredictionScore>()`, assert the `Stake` value carried through (parallel to the existing WinProbability carry-through assertion).
- [ ] `dotnet test` passes.

## Blocked by

None - can start immediately. The handler test constructs its own `TodaysPredictions.csv` (with a `Stake` column) in memory, so it does not depend on the Python side; only the column name `Stake` must match the output of `issues/002`.

## User stories addressed

Reference by number from the parent PRD:

- User story 18 (forward log records the stake advised alongside its outcome)
- User story 20 (logged stakes-and-outcomes make a calibration curve computable later)
