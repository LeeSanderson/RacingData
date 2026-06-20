# Issue 003 — Generalise the write-back

**Type:** AFK

## Parent PRD

`issues/prd.md` — see *Write-back (the `validate` command handler)* under Implementation Decisions, the Testing Decisions write-back bullet, and the Issue C entry in the Delivery / Issue Breakdown.

## What to build

Generalise the existing forecast-odds merge in `ValidateRaceCardPredictions/ValidateRaceCardPredictionsCommandHandler.cs` into a single **race-card-data merge** that copies all six pre-race columns from `TodaysRaceCards.csv` into the matching `(RaceId, HorseId)` rows of the results files, when today's predictions are validated and scored.

Mechanism (identical in spirit to the forecast-odds precedent):

- One read of `TodaysRaceCards.csv`, one write per results file.
- Drop the global "only runners with a forecast price" qualifying filter. Instead index **all** card runners by `(RaceId, HorseId)`; for each result row matched on that key, copy **each** target column **only if** the card value is present (non-null / non-empty) **and** the result cell is currently blank (per-field presence + per-field blank-fill).
- Source→target for ratings: card `OfficialRating` → result `CardOfficialRating`, card `RacingPostRating` → `CardRacingPostRating`, card `TopSpeedRating` → `CardTopSpeedRating`. The four base fields (`DaysSinceLastRun`, `FormFigures`, `PrizeMoney`, `PrizeMoneyValue`) map name-to-name.
- The existing forecast-odds blank check (its two-column rule) is **preserved exactly**, so forecast-odds behaviour is unchanged — this is purely additive.
- A results file is rewritten **only when at least one cell was filled**.

Forward-only and idempotent by construction: historical rows stay blank, and re-running `validate` on the same day fills nothing new.

## Acceptance criteria

- [ ] Running the `validate` handler copies blank result cells from the matching card row by `(RaceId, HorseId)` across all six columns (the three `Card*` ratings + the four base fields).
- [ ] Already-populated result cells are **not** overwritten (per-field idempotency) — re-running `validate` is a no-op on filled cells.
- [ ] A field absent on the card leaves the corresponding result cell blank (per-field presence); an unrated race with a forecast, or a rated race without one, still fills whatever data it does have.
- [ ] The `Card*` ratings are sourced from the card's pre-race OR/RPR/TSR, not the post-race result figures.
- [ ] Existing forecast-odds merge behaviour is unchanged (its two-column blank rule still holds), and a results file is rewritten only when at least one cell was filled.
- [ ] `ValidateRaceCardPredictionsCommandHandlerShould` (prior art for the forecast-odds merge) is extended to cover the above; `dotnet build && dotnet test` passes.

## Blocked by

- Blocked by `issues/002-surface-fields-in-csv-records.md`

## User stories addressed

- User story 9 (reuse the forecast-odds mechanism, single card→result path)
- User story 10 (idempotent, fill only blank cells)
- User story 11 (keyed on `(RaceId, HorseId)`)
- User story 12 (each field copied independently — per-field presence AND per-field blankness)
- User story 13 (existing forecast-odds behaviour preserved exactly; purely additive)
- User story 20 (new columns ignored by current feature engineering — verified by the additive, no-Python-change nature of the write-back)
