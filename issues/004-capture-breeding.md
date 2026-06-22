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

- [ ] `RaceDataDownloader.exe downloadtodaysracecards --output Data` (via `.\run.ps1`) produces
      `TodaysRaceCards.csv` with new trailing columns `SireName` (idx 40), `SireCountry` (idx 41),
      `DamName` (idx 42).
- [ ] `RaceRunner` exposes a breeding value object populated from the JSON view; the slice-001
      reader exposes `sireName` / `sireCountry` / `damName` with vanished-key-throws /
      null-value-clean semantics.
- [ ] `DownloadTodaysRaceCardsCommandHandlerShould` Verify snapshot is updated to include the three
      breeding columns, populated from fixture data (sample `Time Test` / `GB` per the audit).
- [ ] Owner columns (idx 38–39) and all earlier columns are unchanged in position and value.

## Blocked by

- Blocked by `issues/003-capture-owner.md`

## User stories addressed

- User story 2 (sire and sire-country captured)
- User story 3 (dam captured alongside sire)
- User story 17 (new columns appended to the end of `TodaysRaceCards.csv`)
