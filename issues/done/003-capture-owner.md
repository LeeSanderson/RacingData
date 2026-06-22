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

- [x] `RaceDataDownloader.exe downloadtodaysracecards --output Data` (via `.\run.ps1`) produces
      `TodaysRaceCards.csv` with new trailing columns `OwnerId` (idx 38) and `OwnerName` (idx 39).
      *(`.\run.ps1` not executed — needs live Puppeteer/network; the `DownloadTodaysRaceCards`
      handler-level Verify snapshot is the PRD-endorsed faithful proxy, same exception slices 001/002
      took. The snapshot now carries both owner columns.)*
- [x] `RaceRunner` exposes an `Owner` `RaceEntity` populated from the JSON view; the slice-001
      reader exposes `ownerId` / `ownerName` and a missing owner *key* throws while a null owner
      value is written as a clean null.
- [x] `DownloadTodaysRaceCardsCommandHandlerShould` Verify snapshot is updated to include the two
      owner columns, populated from fixture data.
- [x] A backfill cross-reference to `issues/todo.md` is recorded in the code/comment near the owner
      capture; no historic `Results` backfill is performed.
- [x] Existing columns (idx 0–37) are unchanged in position and value.

## Completion note (2026-06-22)

Owner threaded end-to-end from the `__NEXT_DATA__` JSON island to two new trailing `TodaysRaceCards.csv`
columns. Capture only — no Python / feature work; no historic `Results` backfill performed.

Key decisions:
- **Reader:** `ownerId` / `ownerName` added to `NextDataRunner` and to `SentinelKeys`, so a *vanished*
  owner key throws (structural) while a present-but-null owner stays a clean null. `ValidRunner` test
  baseline + the clean-null test were extended; a new `ThrowNamingTheKeyWhenTheOwnerKeyIsMissing` test
  pins the throw.
- **Domain:** `RaceRunner.Owner` is a nullable `RaceEntity`, added as a **trailing optional** ctor
  parameter so the DOM-oracle parser (`RaceCardRunnerParser`) and the cross-validator test are
  unaffected. Owner is excluded from the JSON↔DOM oracle set (the DOM never reads it), so leaving it
  null on the oracle reading is correct.
- **Mapper:** `NextDataRunnerMapper` builds `Owner`; when *both* `ownerId` and `ownerName` are null it
  stays a clean null (no `0`/empty entity). The backfill cross-reference to `issues/todo.md` lives here.
- **CSV:** `OwnerId` `[Index(38)]` / `OwnerName` `[Index(39)]` appended `[Optional]` to `RaceCardRecord`,
  immediately after `PrizeMoneyValue`. **Required follow-on:** `RaceResultRecord : RaceCardRecord`, and
  the base's idx 38/39 collided with the results layout's `RaceTime`(38)/`RaceTimeInSeconds`(39). Owner
  was re-declared with `new` at idx 49/50 — the same shadowing pattern the results layout already uses
  for `DaysSinceLastRun`..`PrizeMoneyValue` — so no existing result column moved. Owner is blank in the
  results layout (no backfill).

Files changed:
- `RacePredictor.Core/RaceRunner.cs` (+optional `Owner`)
- `RacePredictor.Core/RacingPost/NextDataRaceCardView.cs` (+`OwnerId`/`OwnerName` on `NextDataRunner`)
- `RacePredictor.Core/RacingPost/NextDataRaceCardReader.cs` (+owner sentinels + reads)
- `RacePredictor.Core/RacingPost/NextDataRunnerMapper.cs` (+`ToOwner`, backfill cross-ref)
- `RaceDataDownloader/Models/RaceCardRecord.cs` (+idx 38/39)
- `RaceDataDownloader/Models/RaceResultRecord.cs` (+`new` owner at idx 49/50 to avoid collision)
- `RacePredictor.Core.Tests/RacingPost/NextDataRaceCardReaderShould.cs` (owner asserts + missing-key test)
- `RaceDataDownloader.Tests/Models/RaceCardRecordShould.cs` (owner round-trip / legacy-null / fixture)
- 7 `*.verified.txt` snapshots regenerated (card layouts: owner populated; results layouts: owner blank)

Feedback loops: `dotnet build` 0 errors + `dotnet test` green (117 C# tests: 80 Core + 37 RaceDataDownloader).
No Python surface touched.

Next iteration: issue 004 (capture breeding — `SireName`/`SireCountry`/`DamName`, idx 40–42) is now unblocked.

## Blocked by

- Blocked by `issues/002-json-sole-source-with-dom-oracle.md`

## User stories addressed

- User story 1 (owner id captured for forward owner-strike-rate history)
- User story 17 (new columns appended to the end of `TodaysRaceCards.csv`)
- User story 22 (owner-backfill recorded but not implemented here)
