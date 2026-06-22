# 002 — JSON as the sole runner-extraction source + DOM oracle + strict throwing cross-validation

## Parent PRD

`issues/prd.md` — *Capture the racecard extra-data "go" + "defer" fields (forward capture)*.

## What to build

Make the validated `__NEXT_DATA__` view from slice 001 the **sole source** of captured runner data,
and turn the existing DOM parser into a cross-validation oracle. See PRD *Solution* point 1 and
*Implementation Decisions → "JSON is the sole runner-extraction path"* / *"The existing DOM
`RaceCardRunnerParser` is kept unchanged, but only as a cross-validation oracle"* / *"Strict
cross-validation against the DOM oracle"*.

Refactor the runner-extraction entry point (`RaceCardParser.GetRunners` →
`RaceCardRunnerParser.Parse`) so each `RaceRunner` — **all existing fields** (horse/jockey/trainer
id+name, age, weight, headgear, draw, days-since, form figures, OR/RPR/TSR, forecast odds) — is built
from the typed JSON view. Captured data only ever comes from validated JSON.

Keep `RaceCardRunnerParser` (the DOM parser) **unchanged** and run it in parallel purely as an
oracle: it produces a second, independent reading of the overlapping fields that is **never**
written to the CSV. For the curated oracle set of fields the DOM reads robustly (excluding brittle
`<sup>`-derived values), compare JSON-derived vs DOM-oracle values per runner. A small per-field
tolerance absorbs benign edge cases (e.g. a single non-runner row); **systematic divergence beyond a
small threshold across runners throws a `ValidationException`** (with a clear message — story 20),
because it means the JSON node being read no longer corresponds to the rendered card. There is
**no automatic DOM fallback** — a JSON failure or a divergence beyond threshold halts the run.

End-to-end this slice must be behaviour-preserving for the **existing** columns: the
`DownloadTodaysRaceCardsCommandHandler` Verify snapshot of `TodaysRaceCards.csv` (and the parsed
runners) must **match the pre-change baseline** for every column that exists today. No new columns
yet — those land in 003–005.

## Acceptance criteria

- [ ] `RaceCardRunnerParser.Parse` (or the runner-extraction entry point) builds each `RaceRunner`'s
      existing fields from slice 001's JSON view; the DOM parsing logic is retained but only invoked
      as the oracle and never written to the CSV.
- [ ] For the curated oracle field set, JSON-derived and DOM-derived values are cross-validated
      per runner with a documented per-field tolerance; a single within-tolerance mismatch (e.g. one
      non-runner edge) does **not** throw.
- [ ] Systematic divergence on overlapping fields beyond the threshold throws a `ValidationException`
      with a message identifying the diverging field(s) — verified by a crafted fixture/test.
- [ ] An absent / corrupt `__NEXT_DATA__` island causes the run to **throw and produce no CSV**
      (no silent DOM fallback), asserted at the command-handler level via `RunAsync`.
- [ ] `DownloadTodaysRaceCardsCommandHandlerShould` Verify snapshot of `TodaysRaceCards.csv` matches
      the pre-change baseline for all existing columns (regression on existing behaviour).
- [ ] `.\run.ps1` (or the `todaysracecards` step) still produces `TodaysRaceCards.csv` with the
      current column set unchanged.

## Blocked by

- Blocked by `issues/001-next-data-reader-deep-module.md`

## User stories addressed

- User story 13 (JSON is the sole captured-data source)
- User story 14 (DOM parser kept intact, run in parallel only as an oracle)
- User story 15 (structural JSON problem / systematic divergence throws and aborts)
- User story 20 (exception carries a clear, specific message)
- User story 21 (a structural RP change stops the run rather than thinning the CSV)
