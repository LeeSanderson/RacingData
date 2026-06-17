# Soft fill-rate signal on the card download

## Parent PRD

`issues/prd-forecast-odds.md`

## What to build

Add a **soft** structure-change signal to the `todaysracecards` flow so a Racing Post markup change that breaks forecast parsing is visible without hard-failing the daily run.

Each run, log the forecast **fill-rate** (how many runners got a forecast vs. total runners). When a non-empty card yields **zero** forecasts, **warn — do not throw**. This is deliberately softer than the existing hard `EnsureGoingDataIsPresent` check in `DownloadTodaysRaceCardsCommandHandler` (`RaceDataDownloader/Commands/DownloadTodaysRaceCards/DownloadTodaysRaceCardsCommandHandler.cs:31`), because the daily run also performs results-update and prediction and must still complete and commit even when odds parsing returns nothing.

See the PRD's "Race-card parsing (extraction stage)" bullet on the soft signal, and user stories 13 and 14.

## Acceptance criteria

- [ ] The `todaysracecards` run logs the forecast fill-rate (e.g. "N of M runners had a forecast").
- [ ] A non-empty card that yields zero forecasts produces a **warning** and the command still completes successfully (no exception thrown).
- [ ] A test (driven through the command's public entry point, or the parser, consistent with existing prior art) asserts that a zero-forecast card warns but does not hard-fail.
- [ ] The existing `EnsureGoingDataIsPresent` hard-fail behaviour is unchanged.

## Blocked by

- Blocked by `issues/001-parse-forecast-odds-onto-todays-race-cards.md`

## User stories addressed

Reference by number from the parent PRD:

- User story 13
- User story 14
