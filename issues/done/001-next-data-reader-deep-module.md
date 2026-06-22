# 001 — `__NEXT_DATA__` reader deep module + throwing schema validation

## Parent PRD

`issues/prd.md` — *Capture the racecard extra-data "go" + "defer" fields (forward capture)*.

## What to build

The foundational deep module at the heart of this PRD: a `__NEXT_DATA__` reader (in the spirit of
`RacePredictor.Core/RacingPost/RacingResultParser.Parse`) that locates the Next.js `__NEXT_DATA__`
`<script>` island in a race-card HTML document, deserializes it, navigates to the per-runner array
and the race object, and exposes a **typed, read-only view** — a per-runner lookup keyed by horse
id, plus race-level accessors. See PRD *Implementation Decisions → "New deep module"*.

Scope this slice to the **existing overlapping fields only** (the ones the DOM parser already
produces and that slice 002 will cross-validate): horse / jockey / trainer id+name, age, weight,
draw, days-since, form figures, OR / RPR / TSR, forecast odds. The new go/defer columns are added
field-by-field in slices 003–005, each extending this reader.

The reader's interface is narrow: parse a document, get back a validated view **or throw**. There is
**no "degrade to DOM" path** — that decision lives in slice 002, and this module never silently
returns a partial view on a structural problem.

Schema validation is **fail-loud** (PRD *Implementation Decisions → "Schema validation throws"* and
*"Missing key vs null value"*). Before exposing the view the reader asserts the expected shape and
throws a `ValidationException` (mirroring `EnsureGoingDataIsPresent` in
`DownloadTodaysRaceCardsCommandHandler`) with a **specific message** naming the offending
key / path / type (story 20) when any of these occur:

- the `__NEXT_DATA__` `<script>` is absent or its content is unparseable JSON;
- the runners array does not resolve at the expected path, or resolves empty;
- a sentinel set of expected keys is missing from a runner (structural change);
- a consumed field has an unexpected type.

A **present key with a null value** is legitimate data (a flag that did not fire, a jurisdiction
without the field) — it is surfaced as a clean null and must **never** throw. This module owns the
throw on a *vanished* field; the fill-rate canary added later (slice 005) is informational only.

This slice does **not** wire the reader into the command handler and does **not** change
`TodaysRaceCards.csv`. It is verified by its own unit tests rather than `.\run.ps1` — the single
deliberate exception to the demoable-via-pipeline rule, because it is the deep module everything
else builds on.

Lives in `RacePredictor.Core/RacingPost/` alongside the existing parsers.

## Acceptance criteria

- [x] A new reader type exists under `RacePredictor.Core/RacingPost/` that takes a race-card
      `HtmlDocument` (or HTML string) and returns a typed read-only view: per-runner lookup keyed by
      horse id exposing the existing overlapping fields, plus race-level accessors.
- [x] Against all five committed fixtures (`RacePredictor.Core.Tests/RacingPost/Examples/racecard_*_20260520*.html`)
      the reader resolves the runners array and exposes the existing fields, with values matching
      those the DOM `RaceCardRunnerParser` produces for the same cards (Verify snapshot or explicit
      assertions).
- [x] Coverage-edge fixtures parse without throwing: Happy Valley (HK — trainer win-rate badge
      absent) and Gowran Park (IRE, unrated) both yield a valid view.
- [x] Feeding HTML with the `__NEXT_DATA__` script **removed** throws a `ValidationException`
      (not a null/empty view).
- [x] Feeding HTML whose `__NEXT_DATA__` JSON is **present but malformed** (a) missing a sentinel
      key, (b) with the runners array moved/renamed, or (c) with a consumed field of the wrong type
      each throw a `ValidationException` whose message identifies the offending key / path / type.
- [x] A runner whose expected key is **present with a null value** is exposed as a clean null and
      does **not** throw.
- [x] Tests follow the `RaceCardParserShould` / `FakeData.*` fixture pattern in
      `RacePredictor.Core.Tests`.

## Completion note (2026-06-22)

Done. New deep module `RacePredictor.Core/RacingPost/NextDataRaceCardReader.cs` + view
`NextDataRaceCardView.cs` (`NextDataRaceCardView` / `NextDataRunner`, both public — the test project
has no `InternalsVisibleTo`, and the module is tested directly). JSON read via `System.Text.Json`
(net9.0 shared framework — no new package). Runners resolve at
`props.pageProps.initialState.racePage.data.runners`; race identity at `…data.race`
(`raceId` int, `courseId` string, `countryCode`). 18 tests in `NextDataRaceCardReaderShould`; full
suite green (109 C# tests).

**Key findings the cross-validation in 002 must account for** — the DOM `RaceCardRunnerParser` is
buggy on three fields where the JSON is authoritative, so they are deliberately **excluded** from
the JSON↔DOM value comparison (each pinned to known-good values in its own test instead):
- **Age** — DOM `(\d+)yo` row-text regex mis-fires (reads 13 for a 3yo at Gowran).
- **TopSpeedRating** — DOM `(-|\d+)` regex discards genuine negative TSR (e.g. `-5` → null).
- **TrainerName** — HtmlAgilityPack leaves entities undecoded (`"Kim Bailey &amp; Mat Nicholls"`);
  JSON yields the clean `&`. Slice 002 will therefore *correct* these CSV values — expected, not a
  regression; size the cross-validation tolerance accordingly.

**Field-mapping facts for slices 002–005:**
- `forecastOddsValue` is the fractional **ratio** (`"11/2"`→5.5); decimal odds = ratio **+ 1**.
- Horse name gets a country suffix iff `countryOrigin != race.countryCode` (verified 0 mismatches).
- Jockey name embeds a claimer's allowance as `" (N)"` from `weightAllowanceLbs` (read internally
  here for name fidelity; exposed as its own column in 005).
- Ratings are int-or-`"-"`; `daysSinceLastRun` is a string; `formFiguresData` is an ordered
  `{figure,isBold,position}` array joined to e.g. `"3-1958"`; `draw` is present-but-null on jumps.
- The active-runner set = entries with `nonRunner == false && irishReserve == false`, which
  reconciles exactly with the DOM's runner count on every fixture.

The reader is NOT yet wired into the command handler and `TodaysRaceCards.csv` is unchanged
(slice 002+). Verified by unit tests rather than `.\run.ps1`, per the issue.

## Blocked by

None - can start immediately.

## User stories addressed

- User story 13 (JSON read as the source surface)
- User story 15 (structural JSON problem throws)
- User story 16 (missing key throws; present-but-null stays clean)
- User story 20 (structural-change exception carries a specific message)
