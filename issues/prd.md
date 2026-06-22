# PRD — Capture the racecard extra-data "go" + "defer" fields (forward capture)

> Companion to the research deliverable [`../docs/racecard-extra-data-audit.md`](../docs/racecard-extra-data-audit.md).
> That audit ranked every ignored pre-race signal on the Racing Post card; this PRD turns its
> **go** and **defer** verdicts into captured columns. The **no-go** rows (booking-count `<sup>`,
> silks image, weather, race-conditions prose, advisory info) and the **out-of-scope** live-odds
> row are explicitly excluded. The race-level **RP Verdict** (#15, a defer) is also deferred to a
> future text/NLP PRD per the parse-path decision below.

## Problem Statement

The `todaysracecards` scraper writes a daily `TodaysRaceCards.csv`, but **card capture has no
archive** — Racing Post serves only *today's* cards, and there is no historical card store to
re-pull from. So for any pre-race field the scraper does not capture today, that day's value is
**lost forever**. The audit established that the card page exposes a sizeable set of pre-race
signals the scraper currently ignores — owner, breeding (sire/dam), first-time headgear / gelding,
wind-surgery, trainer current form (`trainerRtf`), jockey claim, jockey first-time, new-trainer
count, country of origin, and the per-runner Spotlight prose — and that **none of them is
leakage-suspect** and **none is members-gated** (confirmed from logged-out live pulls).

The catch the audit flagged: every one of these is **forward-only** (no archive), so each yields
*zero* training rows until forward data accrues. That makes the timing argument decisive — the
modelling value of several fields is genuinely deferred, but the **decision to start capturing them
cannot wait**, because every day of delay is a permanent gap in the eventual training set. We need
to begin banking these fields now, even the ones we will not model for a while.

A second problem surfaced during the audit: the high-value fields all live in the page's
`__NEXT_DATA__` JSON island, but the current runner parser scrapes the **rendered DOM** and never
reads that JSON. Bolting individual JSON reads onto a DOM-oriented parser would be awkward and would
leave us maintaining two extraction idioms.

## Solution

Two coordinated changes, shipped together:

1. **Migrate runner extraction to read the `__NEXT_DATA__` JSON island as the sole source of
   captured data**, and **fail the run loudly on any JSON problem** rather than degrading silently.
   The JSON path is the only source for *all* runner fields (existing ones — horse/jockey/trainer,
   age, weight, headgear, draw, days-since, form figures, OR/RPR/TSR, forecast odds — and the new
   ones). The existing DOM parser is **retained unchanged, but only as a cross-validation oracle** —
   it is run in parallel to produce a second, independent reading of the overlapping fields, and its
   output is **never** used as captured data. The two are **strictly cross-validated**: a
   missing/renamed key, a moved runners-array path, a changed field type, an entirely absent island,
   or **systematic JSON↔DOM divergence** on the overlapping fields each **throw a validation
   exception and abort the run** (mirroring the existing `EnsureGoingDataIsPresent` hard check).
   There is **no automatic DOM fallback** — capture comes from validated JSON or the run fails.
   This is deliberate: silently degrading to DOM would null the new columns indefinitely without
   anyone noticing, the exact lost-data failure this PRD exists to prevent. Only *legitimate* data
   absence (a flag that did not fire, a jurisdiction that genuinely lacks a field) stays a clean null
   and never throws.

2. **Append the audited go + defer fields as new trailing columns** on `TodaysRaceCards.csv`. This
   is *capture only* — the columns are populated daily from today's cards and start accruing forward
   history immediately. **No Python feature engineering is in scope**; deriving model features from
   these columns is left to follow-on work, exactly because the point of this PRD is to stop the
   bleeding of lost days while the modelling can come later.

From the punter's point of view nothing changes yet — `TodaysPredictions.csv` is unaffected. From
the data pipeline's point of view, `TodaysRaceCards.csv` grows ~14 columns that begin filling today.

### Fields captured (from the audit verdicts)

All are per-runner reads from the `__NEXT_DATA__` runner object. Verdict tier in brackets; audit row
in parentheses.

| New column(s) | `__NEXT_DATA__` key | Tier | Note |
|---|---|---|---|
| `OwnerId`, `OwnerName` | `ownerId` / `ownerName` | go (1) | Identity key; only **backfill-able** field (backfill itself out of scope — see below) |
| `SireName`, `SireCountry` | `sireName` / `sireCountry` | go (2) | Aptitude signal |
| `HeadgearFirstTime` | `horseHeadGearFirstTime` | go (4) | Bool; complements the static `HeadGear` already captured |
| `GeldingFirstTime` | `geldingFirstTime` | go (5) | Bool; rare-but-strong |
| `WindSurgery` | `windSurgery` | go (6) | Bool; jumps-skewed |
| `TrainerRtf` | `trainerRtf` | go (9) | **Top pick.** Daily-recomputed rolling stat → a **capture-time snapshot**, frozen at capture (no historical reconstruction) |
| `DamName` | `damName` | defer (3) | Cheap add-on to sire |
| `JockeyAllowanceLbs` | `weightAllowanceLbs` | defer (7) | Claimer's allowance |
| `JockeyFirstTime` | `jockeyFirstTime` | defer (8) | Bool |
| `NewTrainerRacesCount` | `newTrainerRacesCount` | defer (11) | Recent yard switch |
| `CountryOfOrigin` | `countryOrigin` | defer (12) | Enum-ish (`GB`/`IRE`/…) |
| `Spotlight` | `spotlight` | defer (14) | **Raw analyst prose banked as text**; no NLP/feature work this PRD |

## User Stories

1. As the owner of the prediction pipeline, I want today's owner id captured for every runner, so
   that a future owner-strike-rate feature has forward history to learn from instead of starting
   from zero.
2. As the owner of the pipeline, I want sire and sire-country captured, so that a future breeding
   aptitude feature can be built for lightly-raced types whose form is thin.
3. As the owner of the pipeline, I want dam captured alongside sire, so that damline aptitude is
   available later at no extra capture trip.
4. As the owner of the pipeline, I want the first-time-headgear flag captured, so that the
   recognised "first-time blinkers/hood sharpener" angle can be modelled once enough fires accrue.
5. As the owner of the pipeline, I want the first-time-gelding flag captured, so that the rare but
   strong post-gelding improvement angle is not lost on the days it does fire.
6. As the owner of the pipeline, I want the wind-surgery flag captured, so that the post-wind-op
   improvement angle (mainly jumps) accrues forward history.
7. As the owner of the pipeline, I want `trainerRtf` captured as a capture-time snapshot, so that
   the best-ranked "yard in form" signal begins building a frozen, leak-free history immediately.
8. As the owner of the pipeline, I want the jockey claim/allowance captured, so that a future
   weight/jockey-interaction feature can use it.
9. As the owner of the pipeline, I want the jockey-first-time-on-horse flag captured, so it is
   available as a free add-on to the other first-time signals later.
10. As the owner of the pipeline, I want the new-trainer races count captured, so the "first runs for
    a new yard" angle accrues history while it is rare.
11. As the owner of the pipeline, I want country of origin captured, so import form-line class is
    available later if it proves useful.
12. As the owner of the pipeline, I want the per-runner Spotlight prose banked as raw text, so that a
    future NLP pipeline has a forward corpus to mine — without committing to any text feature now.
13. As the maintainer of the scraper, I want runner extraction to read the `__NEXT_DATA__` JSON as
    the sole source of captured data, so that every field is a JSON-property read rather than fragile
    DOM scraping.
14. As the maintainer of the scraper, I want the existing DOM parser kept intact and run in parallel
    purely as a cross-validation oracle (never as a fallback), so that the JSON reading can be checked
    against an independent second reading of the page.
15. As the maintainer of the scraper, I want any structural JSON problem — a missing/renamed key, a
    moved runners-array path, a changed field type, an absent island, or systematic JSON↔DOM
    divergence on overlapping fields — to throw and abort the run, so that we never silently capture
    wrong or degraded data.
16. As the maintainer of the scraper, I want a missing expected key to throw (structural change),
    while a present-but-null value stays a logged-informational fill-rate datapoint, so that schema
    drift is fatal but legitimate sparsity is not.
17. As the maintainer of the scraper, I want the new columns appended to the end of
    `TodaysRaceCards.csv`, so that existing column positions and the downstream validate/merge flow
    are undisturbed.
18. As a future modeller, I want the new columns to carry clean nulls when a field is legitimately
    absent or a flag did not fire, so that "field not present" and "flag false" are distinguishable
    downstream — and so that legitimate absence is never confused with a structural failure.
19. As the maintainer, I want the HK and unrated/IRE card shapes handled (win-rate badge absent on
    HK; gelding-first-time trues on Gowran; wind-surgery firing on jumps), so that coverage gaps the
    audit found are treated as clean nulls, not as structural failures.
20. As the maintainer, I want a structural-change exception to carry a clear, specific message
    (which key/path/type or which divergence triggered it), so that a halted daily run can be
    diagnosed and the parser fixed quickly.
21. As the operator of the daily capture, I want a structural RP change to stop the run rather than
    quietly produce a thinner CSV, so that I find out immediately and no day is silently captured
    wrong.
22. As the owner of the pipeline, I want the owner-backfill opportunity recorded but **not**
    implemented here, so that the sibling `todo.md` backfill item remains the single home for that
    work.

## Implementation Decisions

- **New deep module: a `__NEXT_DATA__` reader.** A single module locates the Next.js `__NEXT_DATA__`
  `<script>`, deserializes it, navigates to the per-runner array and race object, and exposes a
  typed, read-only view (per-runner lookup keyed by horse id, plus race-level accessors). Its
  interface is narrow — parse a document, get back a validated view or a clear "not viable" signal —
  and it encapsulates all JSON-navigation detail. This is the deep, independently testable unit at
  the heart of the change (in the spirit of `RacingResultParser.Parse`).
- **JSON is the sole runner-extraction path.** The runner parsing entry point is refactored to build
  each `RaceRunner` (all existing fields **and** the new ones) from the typed JSON view. Captured
  data only ever comes from validated JSON.
- **The existing DOM `RaceCardRunnerParser` is kept unchanged, but only as a cross-validation
  oracle.** It is run in parallel to produce a second reading of the overlapping fields; its output
  is **never** written to the CSV. There is **no automatic fallback** to it — a JSON failure fails
  the run.
- **Schema validation throws (fail loud).** Before trusting the JSON, the reader asserts the expected
  shape: the runners array resolves and is non-empty, a sentinel set of expected keys is present on a
  runner, and each consumed field has the expected type. **Any failed assertion throws a
  `ValidationException` and aborts the run** — it is *not* downgraded to a warning and never triggers
  a DOM fallback. This is the "double-check for JSON schema changes" guardrail, made fatal.
- **Strict cross-validation against the DOM oracle — throws on systematic divergence.** For the
  fields both paths can produce (horse/jockey/trainer id+name, age, weight, draw, days-since, form
  figures, OR/RPR/TSR, forecast odds), the handler compares JSON-derived vs the DOM-oracle values. A
  small per-field tolerance absorbs benign edge cases (e.g. a single non-runner row), but divergence
  beyond a small threshold across runners is treated as structural — **it throws**, because it means
  the JSON node being read no longer corresponds to the rendered card. The oracle set is a curated
  list of fields the DOM parser reads robustly (it excludes brittle `<sup>`-derived values), so the
  check does not false-alarm on known-fragile DOM bits.
- **Missing key vs null value.** A missing/renamed *key* (the structure changed) is caught by schema
  validation and **throws**. A *present key with a null value* (the field legitimately did not apply
  — a flag that did not fire, a jurisdiction without the field) is normal data: it is written as a
  clean null and only logged at the informational fill-rate level (mirroring `LogForecastFillRate` /
  `LogRatingsFillRate`). The fill-rate log is informational only and never throws — the *throw* on a
  vanished field is owned by schema validation, not the fill-rate canary.
- **Domain model additions.** `RaceRunner` gains an `Owner` entity (parallel to horse/jockey/trainer,
  reusing `RaceEntity`). A small value object groups breeding (sire name/country, dam name). The
  remaining per-runner facts (first-time bools, `trainerRtf`, jockey allowance lbs, new-trainer count,
  country of origin, spotlight text) are carried as a runner "extras" value object so the new surface
  is cohesive and testable rather than scattered as loose properties.
- **`TrainerRtf` is a capture-time snapshot.** It is a daily-recomputed rolling stat that excludes
  the current race; it is captured as-is at scrape time and never reconstructed historically. This is
  a *currency* property, not leakage (the value is knowable pre-race) — documented as such.
- **Spotlight is banked verbatim.** The `spotlight` string is stored raw (CSV-escaped) with no
  parsing, trimming of meaning, or feature derivation.
- **Schema change: ~14 new trailing columns on `TodaysRaceCards.csv`**, appended after the current
  last column (`PrizeMoneyValue`), in the same record-mapping style the prior PRD used for
  `DaysSinceLastRun` / `FormFigures` / `PrizeMoney`. No existing column index moves. Columns:
  `OwnerId`, `OwnerName`, `SireName`, `SireCountry`, `DamName`, `HeadgearFirstTime`,
  `GeldingFirstTime`, `WindSurgery`, `TrainerRtf`, `JockeyAllowanceLbs`, `JockeyFirstTime`,
  `NewTrainerRacesCount`, `CountryOfOrigin`, `Spotlight`.
- **Absent vs false.** Bool flags are nullable: null = field/flag absent from the card, false = flag
  present and not set, true = fired. The same null-means-absent rule applies to the numeric/text
  fields.
- **`run.ps1` wiring is unchanged.** The `todaysracecards` step already runs daily; it simply emits
  the wider CSV. No new verb, no new step.
- **No change to the results write-back or `ValidateRaceCardPredictions`.** These read existing
  columns by name/position that are untouched; the new trailing columns are ignored by them.

## Testing Decisions

- **What a good test asserts here:** external behaviour only — the typed view the JSON reader
  exposes, and the CSV the command handler produces — never JSON-navigation internals. Command-level
  tests drive `DownloadTodaysRaceCardsCommandHandler` via `RunAsync` with a fake downloader/loader
  returning fixture HTML and assert on `TodaysRaceCards.csv` (Verify snapshot), exactly as the
  existing `DownloadTodaysRaceCardsCommandHandlerShould` does.
- **The `__NEXT_DATA__` reader is tested in isolation** (it is the new deep module) against the five
  committed card fixtures (`racecard_*_20260520*.html`), which the audit confirmed all embed
  `__NEXT_DATA__`. Cases must cover the audit's coverage edges: HK (Happy Valley) where the trainer
  win-rate badge is absent, Gowran (IRE, unrated) which carries gelding-first-time trues, and a
  jumps card (Warwick hurdles) for wind-surgery.
- **Regression on existing fields:** assert the JSON path reproduces the existing field values the
  DOM parser previously produced (Verify snapshots of the parsed runners / CSV should match the
  pre-change baseline for the existing columns).
- **Absent / corrupt island throws:** feed an input with the `__NEXT_DATA__` script removed or
  unparseable and assert extraction **throws a `ValidationException`** and produces no CSV — it must
  *not* silently fall back to DOM.
- **Schema-change throws:** inputs whose JSON is present but (a) missing a sentinel key, (b) with the
  runners array moved/renamed, or (c) with a consumed field of the wrong type each assert a throw
  with a message identifying the offending key/path/type.
- **Systematic cross-validation divergence throws:** construct an input where JSON and the DOM oracle
  disagree on overlapping fields beyond the threshold and assert a throw; and a companion case where
  a *single* within-tolerance mismatch (e.g. one non-runner edge) does **not** throw, guarding
  against false alarms.
- **Legitimate absence stays a clean null:** assert that a flag that did not fire and a
  jurisdiction-absent field (e.g. HK with no weather-style field) are written as null with **no**
  throw — distinguishing data sparsity from structural failure.
- **Prior art to follow:** `RaceCardParserShould` and the `FakeData.*` fixture pattern in
  `RacePredictor.Core.Tests`; `DownloadTodaysRaceCardsCommandHandlerShould` and
  `ValidateRaceCardPredictionsCommandHandlerShould` (xUnit + Verify) on the handler side.
- **Python side:** untouched, so no pytest work. This is consistent with the codebase's existing gap
  (the Python stage is verified via `.\run.ps1` output, not unit tests) — and there is nothing to
  verify here because no feature engineering is in scope.

## Out of Scope

- **Any Python / feature-engineering work.** No new model features, no `Data/*.py` changes, no
  `Race_Features.csv` or `TodaysPredictions.csv` changes. Capture only.
- **The RP Verdict (#15).** Deferred to a future text/NLP PRD: it is rendered DOM (not JSON), needs
  light NLP for the named selection, and is patchy across cards. Not captured here.
- **Owner backfill into historic `Results`.** Owner is the only backfill-able field, but backfilling
  it is the sibling `todo.md` item *"Backfill form / days-since / prize money into historic Results"*;
  this PRD only forward-captures `OwnerId`/`OwnerName` and records the cross-reference.
- **All no-go rows:** booking-count `<sup>` badge, silks image (needs vision), weather,
  race-conditions prose, advisory info.
- **Live bookmaker odds** — tracked separately in [`../docs/odds-capture.md`](../docs/odds-capture.md)
  (Phase 2), not a new card field.
- **Migrating the race-level parser (`RaceCardParser`) to JSON.** With Verdict deferred there are no
  new race-level columns, so race-level extraction stays on the DOM. JSON migration there is a
  possible future tidy-up, not part of this PRD.
- **Retiring the DOM runner parser.** It is deliberately retained as the cross-validation oracle (not
  a fallback); removing it only becomes a question once the JSON path has proven stable over a long
  window, at which point the cross-validation itself could be relaxed.

## Further Notes

- **Brittleness caveats from the audit carry over.** The `<sup>` styled-component class hashes
  (`sc-25f6462b-7`/`-9`) can rotate on an RP build — another reason `trainerRtf` is taken from JSON,
  not the win-rate `<sup>`. The strict cross-validation is the early-warning system for JSON-shape
  drift, and now it fails the run rather than merely logging.
- **Fail-loud is an accepted operational trade.** Because there is no automatic DOM fallback, a
  structural RP change to the `__NEXT_DATA__` shape will **halt the daily capture** until the parser
  is fixed — a day with no CSV rather than a day of silently-wrong or thinned data. This is the same
  philosophy as the existing `EnsureGoingDataIsPresent` hard check, applied to the whole JSON
  contract: loud failure is preferred to silent corruption, especially given the forward-only,
  no-archive nature of card data. The exception messages (story 20) exist to make that halt quick to
  diagnose. The trade is acceptable precisely because the alternative — quietly nulling the new
  columns — would defeat the PRD's purpose.
- **Forward-only is expected, not a defect.** These columns will be sparsely/again-null on historic
  rows that predate capture; that is the whole reason for starting now. The first useful modelling
  window arrives only after enough forward days accrue — owner is the one field that *could* later be
  retro-filled via the separate backfill item.
- **Coverage realism.** Per the audit, several fields fire sparsely (gelding-first-time, wind-surgery,
  new-trainer count) and some are absent on certain jurisdictions (HK lacks the win-rate badge and
  weather). Capture must treat absence as null and never as an error.
- **Sequencing.** Break-down into vertical-slice issues via the `prd-to-issues` skill; a natural cut
  is: (001) the `__NEXT_DATA__` reader + throwing schema validation as a standalone deep module with
  tests; (002) JSON-as-sole-source runner extraction with the DOM oracle + strict throwing
  cross-validation; (003) the new CSV columns + informational fill-rate logging + end-to-end Verify
  snapshot.
