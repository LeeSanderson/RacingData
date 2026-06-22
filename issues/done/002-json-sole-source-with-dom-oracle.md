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

- [x] `RaceCardRunnerParser.Parse` (or the runner-extraction entry point) builds each `RaceRunner`'s
      existing fields from slice 001's JSON view; the DOM parsing logic is retained but only invoked
      as the oracle and never written to the CSV.
- [x] For the curated oracle field set, JSON-derived and DOM-derived values are cross-validated
      per runner with a documented per-field tolerance; a single within-tolerance mismatch (e.g. one
      non-runner edge) does **not** throw.
- [x] Systematic divergence on overlapping fields beyond the threshold throws a `ValidationException`
      with a message identifying the diverging field(s) — verified by a crafted fixture/test.
- [x] An absent / corrupt `__NEXT_DATA__` island causes the run to **throw and produce no CSV**
      (no silent DOM fallback), asserted at the command-handler level via `RunAsync`.
- [x] `DownloadTodaysRaceCardsCommandHandlerShould` Verify snapshot of `TodaysRaceCards.csv` matches
      the pre-change baseline for all existing columns (regression on existing behaviour).
- [x] `.\run.ps1` (or the `todaysracecards` step) still produces `TodaysRaceCards.csv` with the
      current column set unchanged. *(Verified by construction + the handler Verify regression rather
      than a live scrape — see completion note.)*

## Completion note (2026-06-22)

Done. Runner capture now reads the `__NEXT_DATA__` JSON island as the sole source; the DOM
`RaceCardRunnerParser` is unchanged and run in parallel only as a cross-validation oracle.

**New / changed production code:**
- `NextDataRaceCardReader` / `NextDataRaceCardView` extended (slice 001): added `HeadGear`
  (`horseHeadGear`, now a sentinel key) and `ForecastFractionalOdds`. The fractional price string
  ("11/2") is read from `racePage.data.raceDetails.bettingForecast` (`oddsDesc`, fanned out per
  horse id) — the JSON analog of the DOM betting forecast — so `RaceOdds` reproduces both
  `FractionalOdds` and `DecimalOdds` exactly. A missing forecast is legitimate absence → all SP,
  never throws.
- `NextDataRunnerMapper` (new): builds the captured `RaceRunner[]` from the view — active runners
  only (drops `nonRunner`/`irishReserve`), ordered by card number to match the rendered card order.
- `RaceCardRunnerCrossValidator` (new, deep module, public so it is unit-tested directly): matches
  JSON vs DOM runners by horse id; per-field mismatch tolerance is `> max(1, n/2)` (a single benign
  edge never aborts; majority divergence throws naming the field). Oracle set excludes the
  DOM-buggy/brittle fields **Age, TopSpeedRating, TrainerName, HeadGear** (JSON authoritative). Also
  throws when the JSON runner set does not correspond to the card (too few horse-id matches).
- `RaceCardParser.GetRunners` rewired: read JSON view → map → run DOM oracle → cross-validate → return
  the JSON runners. A reader failure or systematic divergence propagates out and (via the handler's
  existing `try/catch`) aborts the run with `ExitCodes.Error` and no CSV.

**Expected DOM-correction (not a regression):** the Kempton headgear count moves 6 → 7. The old DOM
span-scanning heuristic under-counted by one; JSON `horseHeadGear` is authoritative. This is the same
category as the Age/TSR/TrainerName corrections flagged in slice 001's note (headgear was simply not
read then). It does not touch the HK command-handler Verify snapshot.

**Behaviour preservation:** `RaceCardRecord` and the `.verified.txt` baseline are untouched — no
column added or moved (those land in 003–005). The `DownloadTodaysRaceCardsCommandHandlerShould`
Verify snapshot of `TodaysRaceCards.csv` (Happy Valley) matches the pre-change baseline byte-for-byte,
which is the PRD-endorsed faithful proxy for the `todaysracecards` run.ps1 step (a live Puppeteer
scrape, not run here — same exception slice 001 took).

**Tests:** full suite green — 116 C# tests (79 Core + 37 RaceDataDownloader). New: 5
`RaceCardRunnerCrossValidatorShould` (agreement / single-tolerated / systematic-throws-naming-field /
non-corresponding-set / empty-oracle), 1 reader test (headgear + fractional forecast), 1 handler test
(absent island → Error + no CSV). The previously DOM-mutation `RaceCardParserShould` tests were
retargeted to the JSON contract (reserve exclusion via real HK `irishReserve` flags; SP fallback via
absent betting forecast; Unknown-jockey and null-days via present-but-null JSON values, each a single
tolerated divergence); the DOM-only zero-weight fallback test was dropped (reader maps null → 0, and
null-handling is covered by `NextDataRaceCardReaderShould`).

**Next iteration:** issue 003 (capture owner, CSV idx 38-39) — now unblocked.

## Blocked by

- Blocked by `issues/001-next-data-reader-deep-module.md`

## User stories addressed

- User story 13 (JSON is the sole captured-data source)
- User story 14 (DOM parser kept intact, run in parallel only as an oracle)
- User story 15 (structural JSON problem / systematic divergence throws and aborts)
- User story 20 (exception carries a clear, specific message)
- User story 21 (a structural RP change stops the run rather than thinning the CSV)
