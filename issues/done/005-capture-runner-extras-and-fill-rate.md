# 005 — Capture per-runner extras + fill-rate logging + coverage-edge handling

## Parent PRD

`issues/prd.md` — *Capture the racecard extra-data "go" + "defer" fields (forward capture)*.

## What to build

The final capture slice: forward-capture the remaining nine per-runner extras, add an informational
fill-rate canary for the new fields, and lock in the clean-null behaviour on the audit's coverage
edges. See PRD *Fields captured* (rows 4–12), *Implementation Decisions → "Domain model additions"*
("a runner 'extras' value object so the new surface is cohesive"), *"`TrainerRtf` is a capture-time
snapshot"*, *"Spotlight is banked verbatim"*, *"Absent vs false"*, and *"Missing key vs null value"*.

Thread the extras end-to-end:

- **Reader (slice 001 module):** add typed accessors for `horseHeadGearFirstTime`, `geldingFirstTime`,
  `windSurgery`, `trainerRtf`, `weightAllowanceLbs`, `jockeyFirstTime`, `newTrainerRacesCount`,
  `countryOrigin`, `spotlight` and include them in schema validation (vanished key throws;
  present-but-null stays a clean null).
- **Domain:** add a runner "extras" value object to `RaceRunner` carrying these nine facts. Bool
  flags are **nullable** — null = field/flag absent from the card, false = present and not set,
  true = fired (PRD *"Absent vs false"*).
- **Extraction (slice 002 entry point):** populate the extras VO from the JSON view. `TrainerRtf` is
  captured as-is (a capture-time snapshot, frozen, never reconstructed — a currency property, not
  leakage). `Spotlight` is banked verbatim (raw, CSV-escaped, no parsing/trimming).
- **CSV:** append the nine columns on `RaceCardRecord` after the breeding columns from slice 004, in
  the same `[Optional]` record-mapping style, in this order / index:
  `HeadgearFirstTime` (43), `GeldingFirstTime` (44), `WindSurgery` (45), `TrainerRtf` (46),
  `JockeyAllowanceLbs` (47), `JockeyFirstTime` (48), `NewTrainerRacesCount` (49),
  `CountryOfOrigin` (50), `Spotlight` (51). No existing column index moves.
- **Fill-rate canary:** add informational fill-rate logging for the new fields in
  `DownloadTodaysRaceCardsCommandHandler`, mirroring `LogForecastFillRate` / `LogRatingsFillRate` —
  it logs counts at the information level and **never throws**. (The throw on a vanished field is
  owned by slice 001's schema validation, not this canary.)

Capture only — no Python / feature work; `Spotlight` is banked for a future NLP pipeline with no
text feature derived now.

## Acceptance criteria

- [x] `RaceDataDownloader.exe downloadtodaysracecards --output Data` (via `.\run.ps1`) produces
      `TodaysRaceCards.csv` with the nine new trailing columns `HeadgearFirstTime` … `Spotlight`
      (idx 43–51) in the specified order. *(Verified via the handler Verify snapshot — the header now
      reads `…,DamName,HeadgearFirstTime,GeldingFirstTime,WindSurgery,TrainerRtf,JockeyAllowanceLbs,
      JockeyFirstTime,NewTrainerRacesCount,CountryOfOrigin,Spotlight` — not the live `.\run.ps1`
      scrape, the deliberate exception slices 001–004 took; capture path and column order are fixed by
      construction.)*
- [x] `RaceRunner` exposes an extras value object populated from the JSON view; bool flags are
      nullable with null/false/true distinguishable; `TrainerRtf` is the raw capture-time value and
      `Spotlight` is the verbatim prose.
- [x] `DownloadTodaysRaceCardsCommandHandler` emits an informational fill-rate log line for the new
      fields and never throws on legitimate absence.
- [x] Coverage-edge fixtures are handled as clean nulls, not failures: Happy Valley (HK — win-rate
      badge absent → `TrainerRtf` clean null), Gowran Park (gelding-first-time trues present), Warwick
      (wind-surgery on a jumps card). Verify snapshot / tests assert null vs false vs true is correct on these.
- [x] `DownloadTodaysRaceCardsCommandHandlerShould` Verify snapshot is updated to include all nine
      columns, populated from fixture data; columns idx 0–42 are unchanged in position and value.

## Completion note

Final capture slice shipped, mirroring the slice-003 owner / slice-004 breeding pattern end-to-end.

**Key data-shape correction vs the PRD/audit:** the audit (PRD *Fields captured* row 6) assumed
`windSurgery` was a **bool** flag. The live `__NEXT_DATA__` JSON actually carries it as an **integer**
(Warwick's Mojito Des Mottes → `windSurgery:2`, null otherwise), and `trainerRtf` is likewise an
integer (the trainer current-form snapshot). Both are captured **faithfully as `int?`**, not coerced
to bool — modelling them as bool would have made the reader's fail-loud type check throw on `2`,
aborting the run on a legitimate jumps card. The genuine bool flags (`HeadgearFirstTime`,
`GeldingFirstTime`, `JockeyFirstTime`) are nullable bools with null/false/true distinguishable.
The CSV column name stays `WindSurgery` (issue spec) but its values are the integer / blank.

- **Reader:** 8 new sentinel keys added (`horseHeadGearFirstTime`, `geldingFirstTime`, `windSurgery`,
  `trainerRtf`, `weightAllowanceLbs`, `jockeyFirstTime`, `newTrainerRacesCount`, `spotlight`;
  `countryOrigin` was already a sentinel). New `BoolOrNull` accessor preserves null vs false (the
  existing `Bool` collapses null→false). `weightAllowanceLbs` is now read once via `NumberOrNull` and
  reused for both jockey-name reconstruction and the new `JockeyAllowanceLbs` field; the now-unused
  `NumberAllowingMissing` accessor was removed.
- **Domain:** new `RaceRunnerExtras` value object; `RaceRunner.Extras` added as a TRAILING OPTIONAL
  ctor parameter so the DOM-oracle parser and cross-validator are untouched. Extras are excluded from
  the JSON↔DOM oracle set (the DOM never reads them).
- **Mapper:** `NextDataRunnerMapper.ToExtras` builds the VO; all-null → clean null (rarely fires since
  `CountryOfOrigin` is near-universal).
- **CSV:** `HeadgearFirstTime`(43)…`Spotlight`(51) appended `[Optional]` to `RaceCardRecord`.
  `RaceResultRecord` re-declares all nine with `new` at idx 54–62 (the established shadowing pattern)
  to avoid the base 43–51 colliding with the results layout; blank in results (not backfill-able).
- **Fill-rate canary:** `LogExtrasFillRate` logs per-field presence counts at information level and
  **never warns or throws** (extras are legitimately sparse; the throw on a vanished key is owned by
  the reader's schema validation).
- **Spotlight** is banked verbatim (CSV-escaped by CsvHelper — quoted when it contains commas/quotes;
  `&` decodes to `&`).

**Feedback loops:** `dotnet build` (0 errors) + `dotnet test` green (123 C# tests: 85 Core + 38
RaceDataDownloader). 7 `*.verified.txt` snapshots regenerated (card CSV ×2, card JSON ×1, results CSV
×4; results JSON unchanged — null `Extras` is omitted by the serializer). No Python surface touched.

This was the last capture slice — the forward-capture PRD is now fully implemented.

## Blocked by

- Blocked by `issues/004-capture-breeding.md`

## User stories addressed

- User stories 4, 5, 6 (first-time headgear, first-time gelding, wind-surgery flags)
- User story 7 (`TrainerRtf` capture-time snapshot)
- User stories 8, 9 (jockey allowance/claim, jockey-first-time flag)
- User story 10 (new-trainer races count)
- User story 11 (country of origin)
- User story 12 (Spotlight prose banked as raw text)
- User story 16 (present-but-null is an informational fill-rate datapoint, not a throw)
- User story 17 (new columns appended to the end of `TodaysRaceCards.csv`)
- User story 18 (clean nulls so "field absent" and "flag false" are distinguishable)
- User story 19 (HK / Gowran / Warwick coverage edges treated as clean nulls)
