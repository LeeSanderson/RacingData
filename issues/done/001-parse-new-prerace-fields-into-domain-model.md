# Issue 001 — Parse new pre-race fields into the domain model

**Type:** AFK

## Parent PRD

`issues/prd.md` — see *Domain model* and *Parsing (racecard parsers only)* under Implementation Decisions, and the Issue A entry in the Delivery / Issue Breakdown.

## What to build

Capture three additional pre-race fields off the Racing Post racecard into the `RacePredictor.Core` domain model, parsed by the racecard parsers only:

- `PrizeMoney` — **race-level**. Captured twice: the raw display string (currency symbol + thousands separators preserved) and a numeric value (symbol and commas stripped). Currency is **not** normalised across countries.
- `DaysSinceLastRun` (`int?`) and `FormFigures` (`string?`) — **per-runner**, parsed from the racecard runner rows.

All three are added to the relevant attributes types as **optional, defaulted-null constructor parameters appended after the existing parameters**, so every existing construction path (notably the result parser) keeps compiling unchanged and only the racecard parser populates them.

Parsing uses the existing optional-finder pattern and yields null/empty on absence. Absence is normal (first-time runners have no form or days-since; some races show no prize money), so this is **not** guarded by an `Ensure*` / `ValidationException`.

No CSV record change and no write-back change in this slice — those are Issues 002 and 003. Because no CSV columns change here, there is **no Verify snapshot churn** in this issue.

## Acceptance criteria

- [ ] The race-level attributes type in `RacePredictor.Core` gains a `PrizeMoney` (raw string) and a numeric prize-money value, as optional defaulted-null trailing ctor params.
- [ ] The per-runner attributes type in `RacePredictor.Core` gains `DaysSinceLastRun` (`int?`) and `FormFigures` (`string?`), as optional defaulted-null trailing ctor params.
- [ ] The racecard parser populates all four values from the Yarmouth fixture HTML under `Examples/`; existing result-parser construction paths compile and behave unchanged.
- [ ] `RacePredictor.Core.Tests` extends the existing Yarmouth racecard parser test (prior art: `RaceCardParserShould`) to assert `DaysSinceLastRun`, `FormFigures` (raw string), the raw `PrizeMoney` string, and the numeric prize-money value on a known runner.
- [ ] A null/absence test asserts that a first-time runner (no form / no days-since) parses to null/empty rather than throwing — reuse an existing first-timer fixture if one exists, otherwise curate a minimal one.
- [ ] `dotnet build && dotnet test` passes.

## Blocked by

None - can start immediately.

## User stories addressed

- User story 4 (`DaysSinceLastRun` captured from the card)
- User story 5 (`FormFigures` raw string)
- User story 6 (numeric prize-money value as a quality proxy)
- User story 7 (raw `PrizeMoney` string preserved alongside numeric)
- User story 15 (parsing tolerates absence — first-timers, no-prize races)
