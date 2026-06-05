## Parent PRD

`issues/prd.md`

## What to build

Carry `WinProbability` from `TodaysPredictions.csv` through into `PredictionScores_YYYYMM.csv` in the C# `RaceDataDownloader` tool. `TodaysPredictions.csv` already contains `WinProbability` (written by `predict.py`); it just needs to survive the merge-and-score step that produces the history CSV.

Changes required:

- `RaceDataDownloader/Models/RaceCardPredictionScore.cs`: add a nullable `WinProbability` (`double?`) property.
- `ValidateRaceCardPredictionsCommandHandler.cs` (or wherever predictions are merged with results): read `WinProbability` from the `TodaysPredictions.csv` row and populate the new property. When the column is absent from the input (legacy rows), write `null`/empty rather than throwing.
- CSV serialisation: `PredictionScores_YYYYMM.csv` gains a `WinProbability` column (nullable float).

See PRD §PredictionScores WinProbability for full spec.

## Acceptance criteria

- [ ] `PredictionScores_YYYYMM.csv` contains a `WinProbability` column.
- [ ] When `TodaysPredictions.csv` includes `WinProbability`, the value is carried through correctly to the scored row.
- [ ] When `TodaysPredictions.csv` is missing the `WinProbability` column (legacy file), the tool does not throw — it writes null/empty for that column.
- [ ] xUnit test: `TodaysPredictions.csv` fixture **with** `WinProbability` → output row has the value.
- [ ] xUnit test: `TodaysPredictions.csv` fixture **without** `WinProbability` → output row has null/empty, no exception.
- [ ] Existing xUnit test suite passes.

## Blocked by

None — can start immediately.

## User stories addressed

- User story 16
- User story 17
