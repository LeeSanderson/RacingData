# Parse betting-forecast odds onto today's race cards

## Parent PRD

`issues/prd-forecast-odds.md`

## What to build

Make today's race cards carry a **real pre-race price** instead of the `"SP"` placeholder.

`RaceCardRunnerParser` currently hardcodes every runner's odds to `new RaceOdds("SP")` in `ExtractStats` (`RacePredictor.Core/RacingPost/RaceCardRunnerParser.cs:181`). Change the parser to read the server-rendered Racing Post **betting forecast** block (`Section__BettingForecast` containing `Link__BettingForecastHorse` anchors), build a per-card `horseId → forecast price` map keyed off the horse id in each forecast anchor's `href` (`/profile/horse/{id}/...`, the same id pattern the runner anchors use), and assign each runner its forecast — reusing the existing `RaceOdds` value type to derive the decimal from the fractional string. A runner with no matching forecast falls back to the existing `"SP"`/empty default, so a missing price never corrupts a row.

`TodaysRaceCards.csv` has **no schema change** — only the *values* of the existing `FractionalOdds`/`DecimalOdds` columns change (forecast instead of `"SP"`). See the PRD's "Race-card parsing (extraction stage)" and "CSV schema" sections.

Because the `todaysracecards` output changes the moment this lands, the existing Verify `.verified.txt` snapshot(s) for `DownloadTodaysRaceCards` must be updated in this slice to keep the snapshot tests green and document the populated forecast odds.

The soft fill-rate log / zero-forecast warning is intentionally split out into `issues/002-soft-fill-rate-signal-on-card-download.md`; do not add it here.

## Acceptance criteria

- [ ] `RaceCardRunnerParser` reads the betting-forecast block and assigns each runner its forecast price (fractional + derived decimal), removing the hardcoded `new RaceOdds("SP")`.
- [ ] A runner with no published forecast falls back to the existing `"SP"`/empty default.
- [ ] `RaceDataDownloader.exe todaysracecards --output Data` produces a `TodaysRaceCards.csv` whose `FractionalOdds`/`DecimalOdds` hold forecast prices (e.g. `11/2` → `6.5`) for runners that have a forecast, and `SP`/empty for those that don't.
- [ ] `RaceCardParserShould` (in `RacePredictor.Core.Tests`) has new tests over real example card HTML (the Kempton example contains a forecast block) asserting runners receive the expected fractional and derived-decimal forecast, plus a case asserting a runner with no forecast falls back to the default.
- [ ] The `DownloadTodaysRaceCardsCommandHandlerShould` Verify `.verified.txt` snapshot(s) are updated to reflect the populated forecast odds, and the snapshot tests pass.

## Blocked by

None - can start immediately.

## User stories addressed

Reference by number from the parent PRD:

- User story 1
- User story 2
- User story 3
- User story 17
- User story 19
