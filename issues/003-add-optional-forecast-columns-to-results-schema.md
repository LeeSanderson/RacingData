# Add optional Forecast* columns to the results schema

## Parent PRD

`issues/prd-forecast-odds.md`

## What to build

Give `Results_YYYYMM.csv` somewhere to store the morning forecast price **separately** from the post-race SP, without breaking the historical files that predate it.

Add two new trailing columns to the **result record type only** (`RaceDataDownloader/Models/RaceResultRecord.cs`, not the shared `RaceCardRecord` base):

- `ForecastFractionalOdds` (string) at `[Index(40)]`
- `ForecastDecimalOdds` (nullable decimal/`double?`) at `[Index(41)]`

They must be **appended at the highest indices** — never inserted mid-schema — because records are read positionally and renumbering would map old files' columns into the wrong fields. The pre-existing `FractionalOdds`/`DecimalOdds` continue to mean the post-race **SP**; this slice does not change their meaning.

Mark both new columns **optional** at the CSV mapping layer using CsvHelper's `[Optional]` attribute (confirmed available in the pinned CsvHelper 33.1.0). The global CSV reader stays strict for every other column; only these two tolerate absence. Existing historical results therefore load with the columns defaulting to empty and gain real columns the next time a monthly file is rewritten. **No backfill** of historical results.

This slice is schema-only — it does not populate the columns (that is `issues/004-merge-forecast-into-results-in-validate.md`). See the PRD's "CSV schema" section and user stories 4, 5, 11, 12, 16.

## Acceptance criteria

- [ ] `RaceResultRecord` gains `ForecastFractionalOdds` `[Index(40)]` and `ForecastDecimalOdds` `[Index(41)]`, both marked `[Optional]`, with no change to the existing column indices or to `RaceCardRecord`.
- [ ] A test confirms that reading a `Results_*.csv` **without** the two new columns succeeds (the columns default to empty/null), guarding the migration.
- [ ] A test confirms a record with the new columns round-trips (write then read) correctly.
- [ ] Existing commands that read results (`updateresults`, `validate`) still load historical `Results_YYYYMM.csv` files without error.

## Blocked by

None - can start immediately.

## User stories addressed

Reference by number from the parent PRD:

- User story 4
- User story 5
- User story 11
- User story 12
- User story 16
