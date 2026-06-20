# Issue 002 — Surface the fields in the CSV records

**Type:** AFK

## Parent PRD

`issues/prd.md` — see *CSV schema* and the ratings canary bullet under *Parsing* in Implementation Decisions, and the Issue B entry in the Delivery / Issue Breakdown.

## What to build

Expose the pre-race fields in the CSV record types so they are written to `TodaysRaceCards.csv` (at card parse) and become writable in `Results_YYYYMM.csv` (filled later by Issue 003's write-back):

- **Base racecard record** (`RaceDataDownloader/Models/RaceCardRecord.cs`, inherited into results) gains four columns with **no** prefix (no post-race counterpart to collide with): `DaysSinceLastRun` (`int?`), `FormFigures` (`string?`), `PrizeMoney` (`string?`, raw), `PrizeMoneyValue` (`decimal?`).
- **Result record** (`RaceDataDownloader/Models/RaceResultRecord.cs`) gains three result-only columns: `CardOfficialRating`, `CardRacingPostRating`, `CardTopSpeedRating` (`int?`). The `Card` prefix is required because the inherited `OfficialRating`/`RacingPostRating`/`TopSpeedRating` already hold post-race values in results.

All new **result** columns are optional and appended at the highest indices (after the existing forecast-odds columns), mirroring the forecast-odds precedent so older files still load. Both record-projection helpers (card + result) are wired to populate the new fields from the parsed domain model (the base fields come from Issue 001; the `Card*` ratings map from the card's already-parsed pre-race OR/RPR/TSR).

Add a **soft fill-rate canary for the ratings** to the `DownloadTodaysRaceCards` command handler, mirroring the existing forecast fill-rate log: info-level counts, and a warn (never throw) only when a non-empty card yields zero of a field.

This slice does **not** touch the `validate` write-back (that is Issue 003) — here the result columns are simply added to the schema and will be blank until Issue 003 fills them.

## Acceptance criteria

- [ ] `RaceCardRecord` carries `DaysSinceLastRun`, `FormFigures`, `PrizeMoney`, `PrizeMoneyValue`, populated by the card projection helper, and these appear in `TodaysRaceCards.csv`.
- [ ] `RaceResultRecord` carries `CardOfficialRating`, `CardRacingPostRating`, `CardTopSpeedRating` as optional columns appended at the highest indices (after forecast-odds columns).
- [ ] A `Results_YYYYMM.csv` written before this change still loads via the non-strict CSV read (verified by an existing or new `RaceResultRecordShould`-style test).
- [ ] The `DownloadTodaysRaceCards` handler logs info-level fill-rate counts for the three card ratings and warns (does not throw) when a non-empty card yields zero of a field, mirroring the forecast fill-rate canary.
- [ ] Verify `.verified.txt` snapshots for the racecard-download commands (and any results-writing snapshot) are re-accepted with the new columns — expected mechanical churn, not a regression.
- [ ] `dotnet build && dotnet test` passes.

## Blocked by

- Blocked by `issues/001-parse-new-prerace-fields-into-domain-model.md`

## User stories addressed

- User story 1 (`CardRacingPostRating` column)
- User story 2 (`CardTopSpeedRating` column)
- User story 3 (`CardOfficialRating` column)
- User story 8 (fields gathered during existing `todaysracecards` step — no new verb)
- User story 14 (new result columns appended as optional so older files still load)
- User story 16 (soft fill-rate canary for the ratings)
