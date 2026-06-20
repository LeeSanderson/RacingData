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

- [x] `RaceCardRecord` carries `DaysSinceLastRun`, `FormFigures`, `PrizeMoney`, `PrizeMoneyValue`, populated by the card projection helper, and these appear in `TodaysRaceCards.csv`.
- [x] `RaceResultRecord` carries `CardOfficialRating`, `CardRacingPostRating`, `CardTopSpeedRating` as optional columns appended at the highest indices (after forecast-odds columns).
- [x] A `Results_YYYYMM.csv` written before this change still loads via the non-strict CSV read (verified by an existing or new `RaceResultRecordShould`-style test).
- [x] The `DownloadTodaysRaceCards` handler logs info-level fill-rate counts for the three card ratings and warns (does not throw) when a non-empty card yields zero of a field, mirroring the forecast fill-rate canary.
- [x] Verify `.verified.txt` snapshots for the racecard-download commands (and any results-writing snapshot) are re-accepted with the new columns — expected mechanical churn, not a regression.
- [x] `dotnet build && dotnet test` passes.

## Implementation notes (done 2026-06-20)

- **CSV index layout / why `new` shadowing.** CsvHelper here maps by `[Index]` *position*, not header
  name (the `FileSystemExtensions.MissingFieldFound` tolerance proves it). Empirically: write is
  sequential by index order (gaps are NOT padded) while read is absolute-by-index — so an index gap, or
  two members sharing an index, silently reads back a *neighbour's* value. `RaceResultRecord : RaceCardRecord`
  shares one index space, and the result type already occupies 34-41. So the four base fields sit at
  `[Index(34-37)]` on `RaceCardRecord` (TodaysRaceCards.csv is rewritten daily — no historical layout to
  preserve, contiguous round-trip) and are re-declared with `new` at `[Index(42-45)]` on `RaceResultRecord`
  (appended after the forecast columns, [Optional]); `Card*` ratings follow at 46-48. CsvHelper's auto-map
  binds the most-derived property, so the hidden base index is ignored and no column is duplicated
  (verified by `RaceResultRecordShould.RoundTripCardDataColumnsThroughCsv`). No `FileSystemExtensions` /
  ClassMap change was needed.
- **`Card*` and base fields are blank in results for now** — `ListFrom(RaceResult)` does not populate
  them (result pages show post-race figures); the validate write-back fills them in Issue 003.
- **Ratings canary fires per-field (faithful to "zero of a field").** The Happy Valley fixture is a Hong
  Kong card that legitimately has **no TopSpeedRating** for any runner, so the canary correctly warns
  "no TSR". In production the `todaysracecards` step sums across all of the day's cards (UK/Irish flat
  carry TSR), so TSR is normally > 0 — but an all-HK/all-jumps day would emit a soft (never-throwing) TSR
  warning. If that proves noisy, a future tweak could exclude TSR or warn only on an all-ratings-zero card.
  The existing forecast test was narrowed to assert *no forecast warning* (it was over-broadly asserting no
  warnings at all).

## Blocked by

- Blocked by `issues/001-parse-new-prerace-fields-into-domain-model.md`

## User stories addressed

- User story 1 (`CardRacingPostRating` column)
- User story 2 (`CardTopSpeedRating` column)
- User story 3 (`CardOfficialRating` column)
- User story 8 (fields gathered during existing `todaysracecards` step — no new verb)
- User story 14 (new result columns appended as optional so older files still load)
- User story 16 (soft fill-rate canary for the ratings)
