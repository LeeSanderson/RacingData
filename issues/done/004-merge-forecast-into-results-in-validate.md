# Merge yesterday's forecast into yesterday's results inside `validate`

## Parent PRD

`issues/prd-forecast-odds.md`

## What to build

Fold the forecast→results merge into the existing `validate` command (`ValidateRaceCardPredictionsCommandHandler`) rather than adding a new verb. `validate` already runs at the correct pipeline moment — after `updateresults` and before `todaysracecards` overwrites the card file — so at that point `TodaysRaceCards.csv` still holds **yesterday's** card and the results have just been refreshed with **yesterday's** results.

Extend `validate` to read the current `TodaysRaceCards.csv` and the relevant month's `Results_YYYYMM.csv`, fill `ForecastFractionalOdds`/`ForecastDecimalOdds` for rows matched on **(RaceId, HorseId)** — the same key the scorer's result lookup already uses (`EnsureResultsLoadedFor` / `FindResultForPrediction`) — and rewrite the results file.

The merge must be:

- **Idempotent**: fill the forecast columns only where they are currently blank, and only where the card carries a real forecast (non-null decimal). A re-run must not overwrite good data with nothing.
- **Resilient**: skip gracefully if either the card file or the results file is absent.
- **Forward-only**: no backfill of historical results.

Accepted residual behaviour: a result that settles in a *later* run (after the card has been overwritten) will not receive a forecast. This is by design — keep the simple ephemeral same-run merge; do not introduce a persisted per-day card-odds archive.

See the PRD's "Merge (folded into `validate`)" section and user stories 6, 7, 8, 18, 20.

## Acceptance criteria

- [ ] `RaceDataDownloader.exe validate --output Data` fills `ForecastFractionalOdds`/`ForecastDecimalOdds` in the month's `Results_*.csv` for rows matched on `(RaceId, HorseId)` against `TodaysRaceCards.csv`, and rewrites the file.
- [ ] Tests driven through the `validate` command's public `RunAsync` entry point assert on the produced `Results_*.csv`, covering: (a) forecast populated for matched rows; (b) idempotent re-run leaves already-populated rows untouched; (c) missing card file is handled gracefully; (d) a runner present in results but absent from the card forecast is left unfilled.
- [ ] Only blank forecast cells are filled, and only when the card carries a real (non-null decimal) forecast.
- [ ] The existing prediction-scoring behaviour of `validate` is unchanged.

## Blocked by

- Blocked by `issues/001-parse-forecast-odds-onto-todays-race-cards.md`
- Blocked by `issues/003-add-optional-forecast-columns-to-results-schema.md`

## User stories addressed

Reference by number from the parent PRD:

- User story 6
- User story 7
- User story 8
- User story 18
- User story 20
