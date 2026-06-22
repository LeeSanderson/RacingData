# 004 — Capture breeding (`SireName`, `SireCountry`, `DamName`)

## Parent PRD

`issues/prd.md` — *Capture the racecard extra-data "go" + "defer" fields (forward capture)*.

## What to build

Forward-capture per-runner breeding. See PRD *Fields captured* (rows 2 & 3 — sire is go, dam is a
cheap defer add-on) and *Implementation Decisions → "Domain model additions"* ("A small value object
groups breeding (sire name/country, dam name)").

Thread breeding end-to-end:

- **Reader (slice 001 module):** add typed accessors for `sireName` / `sireCountry` / `damName` to
  the per-runner view and include them in schema validation (vanished key throws; present-but-null
  stays a clean null).
- **Domain:** add a breeding value object (sire name, sire country, dam name) to `RaceRunner`.
- **Extraction (slice 002 entry point):** populate the breeding VO from the JSON view.
- **CSV:** append `SireName` (`[Index(40)]`), `SireCountry` (`[Index(41)]`), `DamName`
  (`[Index(42)]`) as the next trailing columns on `RaceCardRecord`, after the owner columns from
  slice 003, in the same `[Optional]` record-mapping style. No existing column index moves.

Capture only — no Python / feature work. Breeding is **not** backfill-able (absent from result
fixtures), so it is purely forward-only and will be null on historic rows; that is expected.

## Acceptance criteria

- [x] `RaceDataDownloader.exe downloadtodaysracecards --output Data` (via `.\run.ps1`) produces
      `TodaysRaceCards.csv` with new trailing columns `SireName` (idx 40), `SireCountry` (idx 41),
      `DamName` (idx 42). *(Verified by the handler Verify snapshot — the PRD-endorsed faithful proxy;
      `.\run.ps1`'s live Puppeteer scrape was not executed, the same documented exception slices
      001–003 took. The column set is correct by construction.)*
- [x] `RaceRunner` exposes a breeding value object populated from the JSON view; the slice-001
      reader exposes `sireName` / `sireCountry` / `damName` with vanished-key-throws /
      null-value-clean semantics.
- [x] `DownloadTodaysRaceCardsCommandHandlerShould` Verify snapshot is updated to include the three
      breeding columns, populated from fixture data (Happy Valley breeding, e.g. Heroic Master →
      `Not A Single Doubt` / `AUS` / `Jacquetta`).
- [x] Owner columns (idx 38–39) and all earlier columns are unchanged in position and value.

## Completion note

Threaded breeding end-to-end, mirroring the slice-003 owner pattern exactly:

- **Reader:** `sireName` / `sireCountry` / `damName` added to `NextDataRaceCardReader.SentinelKeys`
  (vanished key throws) and read via `StringOrNull` (present-but-null → clean null). `NextDataRunner`
  view gains the three nullable string accessors.
- **Domain:** new `RaceRunnerBreeding` value object (sire name/country, dam name); `RaceRunner.Breeding`
  added as a TRAILING OPTIONAL ctor parameter so the DOM-oracle parser and cross-validator are
  untouched. Breeding is excluded from the JSON↔DOM oracle set (the DOM never reads it) and — unlike
  owner — is **not** backfill-able (absent from result pages).
- **Mapper:** `NextDataRunnerMapper.ToBreeding` builds the VO; when all three fields are null it stays
  a clean null (no all-null VO).
- **CSV:** `SireName` [Index(40)] / `SireCountry` [Index(41)] / `DamName` [Index(42)] appended
  `[Optional]` to `RaceCardRecord` after the owner columns. `RaceResultRecord` re-declares them with
  `new` at idx 51/52/53 (the base's 40–42 collide with the results layout's
  ForecastFractionalOdds(40)/ForecastDecimalOdds(41)/DaysSinceLastRun(42)) — same shadowing pattern as
  owner; breeding stays blank in the results layout (no backfill).

Feedback loops: `dotnet build` (0 errors) + `dotnet test` green (118 C# tests: 81 Core + 37
RaceDataDownloader; +1 vs slice 003 — the new sire-key throw test). Seven `*.verified.txt` snapshots
updated (card layouts: breeding populated; results layouts: breeding blank trailing). No Python
surface touched.

Next iteration: issue 005 (capture per-runner extras + fill-rate logging + coverage edges, idx 43–51)
— now unblocked.

## Blocked by

- Blocked by `issues/003-capture-owner.md`

## User stories addressed

- User story 2 (sire and sire-country captured)
- User story 3 (dam captured alongside sire)
- User story 17 (new columns appended to the end of `TodaysRaceCards.csv`)
