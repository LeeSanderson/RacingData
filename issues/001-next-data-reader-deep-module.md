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

- [ ] A new reader type exists under `RacePredictor.Core/RacingPost/` that takes a race-card
      `HtmlDocument` (or HTML string) and returns a typed read-only view: per-runner lookup keyed by
      horse id exposing the existing overlapping fields, plus race-level accessors.
- [ ] Against all five committed fixtures (`RacePredictor.Core.Tests/RacingPost/Examples/racecard_*_20260520*.html`)
      the reader resolves the runners array and exposes the existing fields, with values matching
      those the DOM `RaceCardRunnerParser` produces for the same cards (Verify snapshot or explicit
      assertions).
- [ ] Coverage-edge fixtures parse without throwing: Happy Valley (HK — trainer win-rate badge
      absent) and Gowran Park (IRE, unrated) both yield a valid view.
- [ ] Feeding HTML with the `__NEXT_DATA__` script **removed** throws a `ValidationException`
      (not a null/empty view).
- [ ] Feeding HTML whose `__NEXT_DATA__` JSON is **present but malformed** (a) missing a sentinel
      key, (b) with the runners array moved/renamed, or (c) with a consumed field of the wrong type
      each throw a `ValidationException` whose message identifies the offending key / path / type.
- [ ] A runner whose expected key is **present with a null value** is exposed as a clean null and
      does **not** throw.
- [ ] Tests follow the `RaceCardParserShould` / `FakeData.*` fixture pattern in
      `RacePredictor.Core.Tests`.

## Blocked by

None - can start immediately.

## User stories addressed

- User story 13 (JSON read as the source surface)
- User story 15 (structural JSON problem throws)
- User story 16 (missing key throws; present-but-null stays clean)
- User story 20 (structural-change exception carries a specific message)
