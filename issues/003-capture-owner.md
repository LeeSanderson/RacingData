# 003 — Capture owner (`OwnerId`, `OwnerName`)

## Parent PRD

`issues/prd.md` — *Capture the racecard extra-data "go" + "defer" fields (forward capture)*.

## What to build

The first new-field capture slice: forward-capture the owner identity for every runner. See PRD
*Fields captured* (row 1, go tier) and *Implementation Decisions → "Domain model additions"*.

Thread `ownerId` / `ownerName` end-to-end:

- **Reader (slice 001 module):** add typed accessors for `ownerId` / `ownerName` to the per-runner
  view and include them in the schema validation so a *vanished* owner key throws (structural), while
  a present-but-null owner stays a clean null.
- **Domain:** add an `Owner` `RaceEntity` to `RaceRunner` (parallel to horse/jockey/trainer, reusing
  `RaceEntity`).
- **Extraction (slice 002 entry point):** populate `RaceRunner.Owner` from the JSON view.
- **CSV:** append `OwnerId` (`[Index(38)]`) and `OwnerName` (`[Index(39)]`) as the next trailing
  columns on `RaceCardRecord`, immediately after `PrizeMoneyValue` (`[Index(37)]`), using the same
  `[Optional]` record-mapping style as `DaysSinceLastRun` / `FormFigures` / `PrizeMoney`. No existing
  column index moves.

This is **capture only** — no Python / feature work. Per story 22, this slice records (does not
implement) the owner-backfill opportunity: leave a code comment / note cross-referencing the
sibling `issues/todo.md` item *"Backfill form / days-since / prize money into historic Results"*
(owner is the one backfill-able field), and **do not** backfill historic `Results` here.

## Acceptance criteria

- [ ] `RaceDataDownloader.exe downloadtodaysracecards --output Data` (via `.\run.ps1`) produces
      `TodaysRaceCards.csv` with new trailing columns `OwnerId` (idx 38) and `OwnerName` (idx 39).
- [ ] `RaceRunner` exposes an `Owner` `RaceEntity` populated from the JSON view; the slice-001
      reader exposes `ownerId` / `ownerName` and a missing owner *key* throws while a null owner
      value is written as a clean null.
- [ ] `DownloadTodaysRaceCardsCommandHandlerShould` Verify snapshot is updated to include the two
      owner columns, populated from fixture data.
- [ ] A backfill cross-reference to `issues/todo.md` is recorded in the code/comment near the owner
      capture; no historic `Results` backfill is performed.
- [ ] Existing columns (idx 0–37) are unchanged in position and value.

## Blocked by

- Blocked by `issues/002-json-sole-source-with-dom-oracle.md`

## User stories addressed

- User story 1 (owner id captured for forward owner-strike-rate history)
- User story 17 (new columns appended to the end of `TodaysRaceCards.csv`)
- User story 22 (owner-backfill recorded but not implemented here)
