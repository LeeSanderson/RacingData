# PRD: Capture additional pre-race racecard data and write it back into results files

## Problem Statement

Racing Post racecards carry pre-race information that is useful for predicting races, but most of it never reaches the training data:

- **Pre-race OR / RPR / TSR ratings** *are* parsed onto `TodaysRaceCards.csv` each morning, but that file is overwritten the next day, so the pre-race values are lost. The monthly `Results_YYYYMM.csv` files — the actual training data — only carry the **post-race** OR/RPR/TSR. RPR and TSR are recomputed after the race and are therefore leaky: they can't be used directly as features (a TSR-gated model once faked 0.78 accuracy against a ~0.265 real anchor).
- **Days since last run, prize money, and form figures** are on the racecard but are not collected at all.

The forecast odds already solved exactly this shape of problem: they are written back from the morning card into the matching result rows by the `validate` step, forward-only and idempotent. We want the same treatment for the rest of the useful pre-race data, so that clean, non-leaky pre-race features accumulate in the results files over time.

## Solution

Extend the racecard collection to capture the additional pre-race fields, and generalise the existing forecast-odds write-back so that — when today's predictions are validated and scored — **all** of the pre-race racecard fields are copied from `TodaysRaceCards.csv` into the matching `(RaceId, HorseId)` rows of the results files.

The mechanism is deliberately identical to the forecast-odds precedent: forward-only (historical rows stay blank), idempotent (only blank cells are filled), keyed on `(RaceId, HorseId)`, and gated so a results file is only rewritten when at least one cell was filled.

Six new columns land in the results files:

- `CardOfficialRating`, `CardRacingPostRating`, `CardTopSpeedRating` — the pre-race ratings as shown on the card. The `Card` prefix distinguishes them from the inherited post-race `OfficialRating`/`RacingPostRating`/`TopSpeedRating`. These are **non-leaky** and may be used directly as features once enough have accumulated.
- `DaysSinceLastRun`, `FormFigures` (raw string), `PrizeMoney` (raw string) + `PrizeMoneyValue` (numeric) — newly collected pre-race data.

ML consumption of the new columns is explicitly deferred: the columns accumulate ground truth first; using them as features is future work once coverage is sufficient.

## User Stories

1. As a modeller, I want the pre-race RPR captured into results as `CardRacingPostRating`, so that I can eventually use a ratings signal as a feature without the post-race leakage that bars the existing `RacingPostRating` column.
2. As a modeller, I want the pre-race TSR captured as `CardTopSpeedRating`, so that the speed signal is available pre-race rather than only as the leaky post-race figure.
3. As a modeller, I want the pre-race official rating captured as `CardOfficialRating`, so that all three ratings have a clean, guaranteed-pre-race provenance and remain symmetric.
4. As a modeller, I want `DaysSinceLastRun` captured directly from the card, so that I have an exact, unclamped layoff figure rather than only the reconstructed-and-clamped `DaysRested` derived from the history stats-join.
5. As a modeller, I want `FormFigures` captured as a raw string, so that recent-form information is preserved cheaply now and can be parsed/encoded later without re-scraping.
6. As a modeller, I want race `PrizeMoneyValue` captured as a number, so that I have a continuous proxy for race quality finer than the coarse `Class`.
7. As a modeller, I want the raw `PrizeMoney` string preserved alongside the numeric value, so that the displayed currency and exact text aren't lost (the numeric column does not normalise currency across countries).
8. As a punter relying on the daily pipeline, I want these fields gathered automatically during the existing `todaysracecards` and `validate` steps, so that no new manual step or CLI verb is introduced.
9. As a maintainer, I want the new write-back to reuse the forecast-odds mechanism rather than a parallel one, so that there is a single, well-understood path for card→result data.
10. As a maintainer, I want the write-back to be idempotent and fill only blank cells, so that re-running `validate` on the same day never corrupts or double-writes data.
11. As a maintainer, I want the write-back keyed on `(RaceId, HorseId)`, so that a runner's card data lands on exactly the right result row.
12. As a maintainer, I want each field copied independently (per-field presence on the card AND per-field blankness on the result), so that an unrated race with a forecast — or a rated race without one — still fills whatever data it does have.
13. As a maintainer, I want the existing forecast-odds behaviour preserved exactly while it becomes one field among several, so that this change is purely additive to the current pipeline.
14. As a maintainer, I want all new result columns appended as optional columns, so that results files written before this change still load.
15. As a maintainer, I want parsing of the new fields to tolerate absence (first-time runners have no form or days-since; some races are unrated or show no prize money), so that the scrape never throws on legitimately missing data.
16. As a maintainer, I want a soft fill-rate log for the ratings (mirroring the forecast-odds canary), so that a future Racing Post markup change that silently zeroes a field is visible in the logs without halting the run.
17. As a future modeller, I want documentation that clearly states `Card*` ratings are pre-race and safe to use directly, while the inherited results ratings remain leaky, so that I don't mistakenly conclude "all ratings are banned" or — worse — feed a leaky column to a model.
18. As a future modeller, I want it documented that these columns are forward-only, so that I know coverage starts at deployment date and historical rows are blank by design.
19. As a maintainer, I want the option of backfilling form/days-since/prize from result pages recorded as a future idea, so that the possibility (those three fields may appear on result pages, unlike the ratings) isn't lost even though it's out of scope now.
20. As the Python pipeline, I want the new columns to be ignored by current feature engineering, so that adding them to the CSVs cannot change today's predictions or leak into the active model.

## Implementation Decisions

### Scope and direction

- **Forward-only.** New columns populate from deployment forward; historical result rows stay blank. No historical re-scrape of racecards.
- The **result parser is not changed.** All six columns are populated by a uniform card→result write-back. (Ratings *must* come from the card because result pages show post-race figures; the other three are kept on the same mechanism for consistency.)
- **Fields captured:** pre-race OR/RPR/TSR (already parsed), days since last run, prize money, form figures. Colour/sex and owner are excluded.

### Domain model (`RacePredictor.Core`)

- Add `PrizeMoney` to the race-level attributes type.
- Add `DaysSinceLastRun` and `FormFigures` to the per-runner attributes type.
- All three are added as **optional, defaulted-null constructor parameters** appended after the existing parameters, so the result-parser construction paths keep compiling unchanged and only the racecard parser populates them.

### Parsing (racecard parsers only)

- Pre-race OR/RPR/TSR are already extracted from the card's runner-stats node — no parser change for ratings.
- Days since last run and form figures are parsed **per runner** from the racecard runner rows; prize money is parsed **race-level** from the racecard.
- Prize money is captured **twice**: the raw display string (preserves currency symbol and thousands separators) and a numeric value (currency symbol and commas stripped). Currency is **not** normalised across countries — a documented caveat.
- All new-field parsing uses the optional finder pattern and yields null/empty on absence. Absence is normal (first-time runners, unrated races, no-prize races) so this is **not** guarded by an `Ensure*`/`ValidationException`.
- A **soft fill-rate canary** for the ratings is added to the today's-racecards command, mirroring the existing forecast fill-rate log: info-level counts, warn (never throw) only when a non-empty card yields zero of a field.

### CSV schema

- **Base racecard record** (inherited into results) gains: `DaysSinceLastRun` (`int?`), `FormFigures` (`string?`), `PrizeMoney` (`string?`, raw), `PrizeMoneyValue` (`decimal?`). No prefix — these have no post-race counterpart to collide with. They appear in both `TodaysRaceCards.csv` (populated at card parse) and `Results_YYYYMM.csv` (populated by write-back).
- **Result record** gains result-only columns: `CardOfficialRating`, `CardRacingPostRating`, `CardTopSpeedRating` (`int?`). The `Card` prefix is required because the inherited `OfficialRating`/`RacingPostRating`/`TopSpeedRating` already hold post-race values in results.
- All new **result** columns are optional and appended at the highest indices (after the existing forecast-odds columns), mirroring the forecast-odds precedent so older files still load.
- The record-projection helpers for both card and result records are wired to populate the new fields from the parsed domain model.

### Write-back (the `validate` command handler)

- The existing forecast-odds merge is **generalised** into a single race-card-data merge: one read of `TodaysRaceCards.csv`, one write per results file.
- The global "only runners with a forecast price" qualifying filter is dropped. Instead, all card runners are indexed by `(RaceId, HorseId)`, and for each result row matched on that key, **each** target column is copied **only if** the card value is present (non-null / non-empty) **and** the result cell is currently blank.
- Source→target for ratings: the card's `OfficialRating` → result `CardOfficialRating`, and likewise for RPR/TSR. The new base fields map name-to-name.
- The existing forecast-odds blank check (its two-column rule) is preserved exactly, so forecast-odds behaviour is unchanged.
- A results file is rewritten only when at least one cell was filled.

### Pipeline wiring

- No new CLI verb and no change to `run.ps1`. The new data rides through on the existing `todaysracecards` (collection) and `validate` (write-back) steps.

### Python / ML

- No Python changes. The results loader uses a non-strict CSV read, so the added columns load harmlessly and are ignored by current feature engineering. ML consumption is future work.

## Testing Decisions

- **What makes a good test here:** assert on external behaviour, not internals — drive the parsers on fixture HTML and assert the parsed values; drive the `validate` handler via its run entry point and assert on the CSV produced.
- **Parser tests** (prior art: `RaceCardParserShould` and the other `RacePredictor.Core.Tests` parser tests using the fixture HTML under `Examples/`): extend the existing Yarmouth racecard test to assert `DaysSinceLastRun`, `FormFigures` (raw string), `PrizeMoney` (raw) and `PrizeMoneyValue` (numeric) on a known runner — the Yarmouth fixture already contains all these nodes, so no new fixture is required for the happy path. Add a null/absence assertion for a first-time runner (reuse an existing fixture if one contains a first-timer, otherwise curate a minimal fixture).
- **Write-back tests** (prior art: `ValidateRaceCardPredictionsCommandHandlerShould`, which already covers the forecast-odds merge): assert that blank result cells are filled from the card by `(RaceId, HorseId)`; that already-populated cells are **not** overwritten (per-field idempotency); that a field absent on the card leaves the result blank; and that the `Card*` ratings are sourced from the card's pre-race OR/RPR/TSR.
- **Snapshot churn is expected:** the Verify `.verified.txt` snapshots for the racecard-download commands (and any results-writing snapshot) gain the new columns. Re-accepting them is a mechanical, expected part of this work, not a regression.
- **Gate:** `dotnet build && dotnet test`. No Python tests are needed because there are no Python changes; this PRD does not touch `Data/*.py`.

## Out of Scope

- Any Python / ML consumption of the new columns — they must accumulate coverage first.
- Changing the result parser (`RaceResultRunnerParser` / `RacingResultParser`).
- Historical backfill of any kind (no re-scraping of past racecards; historical result rows stay blank).
- Colour/sex and owner fields.
- Live market odds capture (Phase 2, tracked separately).
- Normalising prize money across currencies.

## Further Notes

- The three non-rating fields (form figures, days since last run, prize money) are pre-race facts that may also appear on the result pages already scraped daily. If so, they could be backfilled across history by a single re-scrape — unlike the ratings, which are post-race on result pages. This is deliberately deferred and recorded as a future-idea entry in `issues/todo.md`, sibling to the existing "Backfill ForecastDecimalOdds into historic Results" item.
- Documentation updates accompany the change: `docs/data-pitfalls.md` (the `Card*` ratings are pre-race and non-leaky vs the inherited post-race ratings; the forward-only coverage caveat), an `AGENTS.md` one-liner in the no-leakage constraints pointing to `Card*` as the pre-race-safe rating source, and `docs/odds-capture.md` extended to describe the generalised one-mechanism, six-column write-back.

## Delivery / Issue Breakdown

This PRD maps to four vertical-slice issues; A → B → C are sequential, D is independent and done last:

- **Issue A — Parse new pre-race fields into the domain model.** Add `PrizeMoney` (race-level) and `DaysSinceLastRun`/`FormFigures` (per-runner) to the domain model as optional defaulted-null constructor params; parse them in the racecard parsers; parser unit tests including a null/first-timer case. No CSV change, so no snapshot churn.
- **Issue B — Surface the fields in the CSV records.** Add the four base columns to the racecard record and the three result-only `Card*` rating columns to the result record (optional, appended indices); wire both projection helpers; add the ratings fill-rate canary; re-accept snapshots. Depends on A.
- **Issue C — Generalise the write-back.** Turn the forecast-odds merge into the race-card-data merge with per-field presence + per-field blank-fill across all six columns; validate-handler tests. Depends on B.
- **Issue D — Docs.** Update `docs/data-pitfalls.md`, `AGENTS.md`, `docs/odds-capture.md`, and `issues/todo.md`. Independent; do last.
