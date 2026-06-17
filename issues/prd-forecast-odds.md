# PRD: Capture Forecast Odds onto Today's Race Cards and Merge into Results

> **Nature of this PRD:** This is a change to the **C#/.NET extraction stage** plus the daily pipeline wiring. It adds no new CLI verb (it extends `todaysracecards` parsing and the `validate` command), changes the **semantics** of two existing `TodaysRaceCards.csv` columns, adds **two optional columns** to `Results_YYYYMM.csv`, and moves the scheduled run from 06:00 to 09:00. The Python stage is untouched. This is **Phase 1** of a two-phase effort; live (market) odds are **Phase 2** and out of scope here.
>
> **Saved under a non-default filename** (`issues/prd-forecast-odds.md`) deliberately: an unrelated PRD (`issues/prd.md` — Python type-safety/static-analysis) is in flight and must not be overwritten.

## Problem Statement

As the owner of the racing-data pipeline, I want each day's race cards to carry a **pre-race price** for every runner, and I want that price preserved alongside the post-race Starting Price in the results, so that I can later measure how the morning market compares to the SP (value/ROI analysis) instead of only ever having the post-race SP.

Today this is impossible:

- The race-card runner parser **hardcodes** every runner's odds to the literal string `"SP"` (`RaceCardRunnerParser.ExtractStats` → `new RaceOdds("SP")`). It never attempts to read any price, so `TodaysRaceCards.csv` always shows `FractionalOdds = SP` and an empty `DecimalOdds`, regardless of what time the scraper runs.
- The Racing Post race-card page actually carries a server-rendered **betting forecast** (RP's morning "tissue" price, one per runner) that is available when the card is published — but the parser ignores it.
- The **results** files (`Results_YYYYMM.csv`) carry the post-race **SP** in `FractionalOdds`/`DecimalOdds` (parsed from the result page's `rp-horseTable__horse__price`). There is nowhere to store a separate morning price, so even if we captured one on the card it would be lost when results are scored.
- The scheduled run fires at **06:00**, chosen before any odds work; it is the natural place to also start capturing odds, but it currently captures none.

A separate, harder source — the **live bookmaker market** (the Diffusion-fed "betting-odds" tab) — is what is genuinely *unavailable early and may appear later in the morning*. That is real but riskier to capture and is explicitly deferred to Phase 2.

## Solution

From the user's perspective:

1. **Today's race cards gain a real forecast price.** After the change, `TodaysRaceCards.csv`'s existing `FractionalOdds`/`DecimalOdds` columns hold each runner's **betting-forecast** odds (e.g. `11/2` → `6.5`) instead of the placeholder `"SP"`. Runners with no forecast keep the `"SP"`/empty default.
2. **Results gain a separate "forecast" price.** `Results_YYYYMM.csv` gains two new columns — `ForecastFractionalOdds` and `ForecastDecimalOdds` — that preserve the morning forecast captured from the card. The existing `FractionalOdds`/`DecimalOdds` in results continue to mean the post-race **SP** ("final odds"). The two prices now sit side by side.
3. **The merge happens automatically in the daily run.** Because the pipeline updates results and runs `validate` *before* it overwrites the card file, at that moment `TodaysRaceCards.csv` still holds **yesterday's** card and the results have just been refreshed with **yesterday's** results. `validate` is extended to merge yesterday's forecast into yesterday's results at that point.
4. **The run moves to 09:00.** This settles the schedule now so Phase 2 (live odds) only has to add parsing. Phase 1 itself does not need the later slot (the forecast is present at 06:00), but moving once avoids a second schedule change.

This is intentionally phased: **Phase 1 (this PRD) = forecast odds, low capture risk.** **Phase 2 (later) = live market odds**, which require a loader that waits for the post-load Diffusion feed and an empirical check of *when* prices populate.

## User Stories

1. As a pipeline owner, I want today's race cards to record each runner's betting-forecast price, so that I have a pre-race price instead of a `"SP"` placeholder.
2. As a pipeline owner, I want the forecast price expressed both fractionally and as a decimal, so that it is directly comparable to the decimal SP already stored in results.
3. As a pipeline owner, I want runners with no published forecast to fall back to the existing `"SP"`/empty default, so that a missing price never corrupts a row.
4. As a pipeline owner, I want the results files to keep a **separate** forecast price distinct from the SP, so that I never lose the morning price when the SP is recorded.
5. As a pipeline owner, I want the existing `FractionalOdds`/`DecimalOdds` in results to keep meaning the post-race SP, so that historical analysis built on those columns is unaffected.
6. As a pipeline owner, I want yesterday's forecast merged into yesterday's results automatically during the daily run, so that I do not have to run a manual step.
7. As a pipeline owner, I want the merge to join on the same (RaceId, HorseId) key the scorer already uses, so that the matching logic is consistent and correct.
8. As a pipeline owner, I want the merge to fill the forecast columns only where they are blank and only when the card actually has a forecast, so that re-runs are idempotent and never overwrite good data with nothing.
9. As a pipeline owner, I want the daily scheduled run moved to 09:00, so that the schedule is fixed ahead of the Phase 2 live-odds work.
10. As a pipeline owner, I want predictions to keep working when they run ~3 hours later, so that moving the schedule has no functional downside (UK/IRE racing starts well after 09:00).
11. As a pipeline owner, I want existing `Results_YYYYMM.csv` files (which predate the new columns) to keep loading without error, so that the change does not break `updateresults` or `validate`.
12. As a pipeline owner, I want the new results columns to be optional at the CSV layer, so that the reader stays strict for every other column and only the genuinely-new ones are tolerant of absence.
13. As a pipeline owner, I want a per-run log of forecast fill-rate, so that I can see at a glance how many runners got a forecast and detect a Racing Post page-structure change.
14. As a pipeline owner, I do **not** want a forecast-less morning to hard-fail the run, so that the daily results-update and prediction steps still complete and commit even if odds parsing returns nothing.
15. As a data scientist, I do **not** want the forecast price to silently become a model feature, so that I avoid the known leakage trap (odds were previously unavailable at prediction time; now a real price exists on the card at prediction time).
16. As a pipeline owner, I want historical results left as-is (no backfill), so that the change is forward-only and produces no large historical diff.
17. As a maintainer, I want the forecast-parsing logic covered by tests against real example card HTML, so that a Racing Post markup change is caught by a failing test rather than in production.
18. As a maintainer, I want the `validate` merge covered by tests driven through the command's public entry point asserting on the produced results CSV, so that I test behaviour, not internals.
19. As a maintainer, I want the `todaysracecards` approval (`.verified.txt`) snapshots updated to reflect populated forecast odds, so that the snapshot tests remain green and document the new output.
20. As a pipeline owner, I accept that results which settle late and arrive in a *later* run will not receive a forecast (the card has been overwritten by then), so that I keep the simple ephemeral merge and avoid a new persisted file.
21. As a future implementer, I want Phase 2 (live market odds) clearly scoped out with its known blocker recorded (the loader does not wait for the Diffusion feed), so that the live-odds work can start from a clear baseline.

## Implementation Decisions

**Odds source & phasing**
- Capture both forecast and live odds **eventually**, but this PRD delivers **forecast only** (Phase 1). Live market odds are Phase 2.
- The forecast is the server-rendered Racing Post "betting forecast" (the `Section__BettingForecast` / `Link__BettingForecastHorse` block), one price per runner, present when the card is published.

**Race-card parsing (extraction stage)**
- The race-card runner parsing is changed to read the betting-forecast block, build a per-card map of runner → forecast price keyed by horse id (the forecast anchors carry the horse id in their href, matching the runner anchors), and assign each runner its forecast, reusing the existing `RaceOdds` value type to derive the decimal from the fractional string.
- The current hardcoded `"SP"` odds for race-card runners is removed; absence of a forecast for a given runner falls back to the existing `"SP"`/empty default.
- A **soft** structure-change signal is added: log the forecast fill-rate each run and **warn** (do not throw) when a non-empty card yields zero forecasts. This is deliberately softer than the existing hard `EnsureGoingDataIsPresent` check, because the daily run also performs results-update and prediction and must still complete/commit.

**CSV schema**
- `TodaysRaceCards.csv`: **no schema change.** Only the *values* of the existing `FractionalOdds`/`DecimalOdds` columns change (forecast instead of `"SP"`).
- `Results_YYYYMM.csv`: **two new trailing columns** — `ForecastFractionalOdds` (string) and `ForecastDecimalOdds` (nullable decimal) — added to the **result record type only** (not the shared card base), appended at the end of the column order. The pre-existing `FractionalOdds`/`DecimalOdds` continue to hold the SP.
- The new columns are appended at the highest indices and **never** inserted mid-schema, because the records are read positionally; renumbering would map old files' columns into the wrong fields.
- The new columns are marked **optional** at the CSV mapping layer (CsvHelper's `Optional` attribute, confirmed available in the pinned CsvHelper 33.1.0). The global CSV reader stays strict; only these two columns tolerate absence. Existing historical results therefore load with the columns defaulting to empty, and gain real columns the next time a monthly file is rewritten.

**Merge (folded into `validate`)**
- The forecast→results merge is folded into the existing `validate` command rather than a new verb. `validate` already runs at the correct pipeline moment — after `updateresults` and before `todaysracecards` overwrites the card file — so the card on disk is still **yesterday's** and the results have just been refreshed with yesterday's data.
- The merge reads the current `TodaysRaceCards.csv` and the relevant month's `Results_YYYYMM.csv`, fills `ForecastFractionalOdds`/`ForecastDecimalOdds` for rows matched by **(RaceId, HorseId)** — the same key the scorer's result lookup already uses — and rewrites the results file.
- The merge is **idempotent**: it fills the forecast columns only where they are currently blank and only where the card carries a real forecast (non-null decimal). It is resilient to either file being absent (skips gracefully).
- Merge is **forward-only**: no backfill of historical results.

**Scheduling & wiring**
- The Azure DevOps scheduled run (`.azuredevops/scheduled-run.yml`) cron moves from `0 6` to `0 9`.
- `run.ps1` step order is unchanged (`updateresults → validate → todaysracecards → build_features → predict`); the merge rides inside the existing `validate` step.

**Leakage guardrail**
- The card now carries a real forecast price at prediction time. The Python predictor currently ignores card odds, so no leakage occurs today, but this must remain true: the forecast must not become a model feature/filter unless deliberately and safely introduced. The existing `project_odds_unavailable_at_prediction` understanding is now partially outdated and should be revised once this ships.

## Testing Decisions

- **What makes a good test:** assert on externally observable behaviour, not internals. Drive command handlers through their public `RunAsync` entry point and assert on the CSV they produce; drive parsers with real fixture HTML and assert on the parsed model / produced records.
- **Forecast parsing:** add parser tests over existing example race-card HTML (which already contains a betting-forecast block, e.g. the Kempton example) asserting that runners receive the expected fractional and derived-decimal forecast, and that a runner with no forecast falls back to the default.
- **`todaysracecards`:** update the existing approval (`.verified.txt`) snapshot(s) for the today's-race-cards command to reflect populated forecast odds in `FractionalOdds`/`DecimalOdds`.
- **`validate` merge:** add tests driven through the `validate` command asserting that the produced `Results_*.csv` has `ForecastFractionalOdds`/`ForecastDecimalOdds` populated for matched (RaceId, HorseId) rows; include cases for idempotent re-run (already-populated rows untouched), missing card file, and a runner present in results but absent from the card forecast.
- **Schema/optionality:** a test that reading a results CSV **without** the new columns succeeds (the columns default), guarding the migration.
- **Prior art to follow:** `ValidateRaceCardPredictionsCommandHandlerShould`, `DownloadTodaysRaceCardsCommandHandlerShould`, `UpdateResultsCommandHandlerShould`, and the parser tests in `RacePredictor.Core.Tests` using fixture HTML (`FakeData.*` / the `RacingPost/Examples` files), with Verify-based approval snapshots.
- **Python:** untouched in this PRD; no Python tests required.

## Out of Scope

- **Live / market odds (Phase 2):** capturing the Diffusion-fed "betting-odds" tab. Known blocker: the Puppeteer loader navigates with `GoToAsync` (load event) and immediately reads content, so the post-load live feed is not captured; this needs a wait strategy / tab activation / odds endpoint plus an empirical check of *when* prices populate during the morning. Phase 2 will add `Starting*` columns to both card and results.
- **Backfilling historical results** with forecast prices (the data was never captured; impossible).
- **Using forecast odds as a model feature/filter** in the Python predictor (explicitly avoided; leakage-sensitive).
- **Capturing forecast for the non-pipeline `downloadracecards`/`RaceCards.csv` flow** beyond what falls out of the shared parser change.
- **A durable per-day card-odds archive.** Considered and rejected in favour of the ephemeral same-run merge; revisit only if late-settling results prove to be a real loss.

## Further Notes

- **Terminology:** the user's "starting odds" refers to the *morning* price (forecast in Phase 1, live in Phase 2), while "final odds" refers to the post-race **SP** already in results. Note this is the inverse of the literal racing meaning of "Starting Price", so column naming uses `Forecast*` (Phase 1) and will use `Starting*` (Phase 2) to stay explicit.
- **Accepted residual risk:** results that settle after the next 09:00 run won't receive a forecast (card overwritten). Rare for UK/IRE/intl meetings settled by the next morning.
- **Verification carried out during design:** confirmed the forecast block is present and parseable in the example card HTML; confirmed the runner parser hardcodes `"SP"`; confirmed the results parser reads SP from `rp-horseTable__horse__price`; confirmed `predict.py` reads `TodaysRaceCards.csv` but no odds column; confirmed CsvHelper 33.1.0 ships the `Optional` attribute; confirmed the `run.ps1` order makes the card "yesterday's" at the `validate` step.
- **Follow-up after ship:** update the `project_odds_unavailable_at_prediction` note to reflect that a forecast price now exists on the card at prediction time and must be kept out of features.
