# Racecard extra-data audit

> **Status: in progress.** This document is the deliverable of the research-only PRD
> *"Audit extra data available on Racing Post today's race cards"* (`issues/prd.md`). It is
> built in three passes:
> - **Issue 001 (this pass — offline foundation):** the Method note, the raw ignored-`data-testid`
>   appendix, and the *draft candidate inventory* with the columns derivable offline (field /
>   source, backfill-able?). The judgement columns carry explicit stubs.
> - **Issue 002 (live evidence):** fills **Availability** and **Coverage** from two fresh live
>   pulls + the fixtures. Stub marker: `TBD-002`.
> - **Issue 003 (judgement):** fills **Leakage**, **Type & parse difficulty**, **Predictive
>   rationale**, and the **Verdict**; adds the ranked *Recommended-to-capture-next* shortlist.
>   Stub marker: `TBD-003`.
>
> No production code is changed by any pass — this is reference, alongside
> [`odds-capture.md`](odds-capture.md) and [`data-pitfalls.md`](data-pitfalls.md).

## Method

**Goal.** Establish, evidence-first, exactly which pre-race signals the Racing Post card page
exposes that the `todaysracecards` scraper currently ignores — so a follow-on capture PRD can
pick fields off a ranked list without re-auditing the page.

**Technique (three axes).**

1. **`data-testid` inventory + parser diff.** Enumerate every `data-testid` value present in each
   card fixture and subtract the set the existing parsers consume
   (`RacePredictor.Core/RacingPost/RaceCardRunnerParser.cs` and `RaceCardParser.cs`), yielding an
   exhaustive list of **ignored** DOM hooks (see [appendix](#appendix--raw-ignored-data-testid-inventory)).
   Across the 5 card fixtures there are **396** distinct `data-testid` values; the parsers consume
   **19**; **377** are ignored — but the overwhelming majority are page chrome (nav / footer /
   menu / bookmaker-offers / ads). The runner- and race-relevant remainder is the candidate set.
2. **Non-`data-testid` scan — `<sup>` badges.** `RaceCardRunnerParser` explicitly notes but
   **discards** `<sup>` badges on the jockey/trainer anchors. Inspected directly: the jockey and
   trainer anchors each carry a booking-count badge (`<sup class="sc-25f6462b-7">`, a small int)
   and the trainer anchor additionally carries a win-rate badge (`<sup class="sc-25f6462b-9">`,
   e.g. `59%`).
3. **Non-`data-testid` scan — `__NEXT_DATA__` JSON island.** *Key finding.* Every card fixture
   embeds a single Next.js `__NEXT_DATA__` `<script>` whose per-runner objects carry a large set
   of **structured** fields that never reach a `data-testid` in the rendered card. Observed
   per-runner keys include: `ownerId`/`ownerName`, `sireName`/`sireCountry`/`damName`,
   `horseHeadGear`/`horseHeadGearFirstTime`, `geldingFirstTime`, `windSurgery`,
   `weightAllowanceLbs`/`extraWeightLbs`/`weightCarried`, `jockeyFirstTime`, `trainerRtf`,
   `newTrainerRacesCount`, `countryOrigin`, `spotlight`/`spotlightLucky`, `oddsValue`/`oddsDesc`,
   plus the already-captured `officialRatingToday`/`rpPostmark`/`rpTopspeed`. A race-level
   `verdict` key is also present. This matters for the eventual capture PRD: for most soft fields
   the parse path is *read a JSON property*, not *scrape the DOM / run NLP* — which will weigh
   heavily on the Type & parse-difficulty column in issue 003.

**Corpus.**

- *Primary (offline, this pass)* — the 5 full-page card fixtures in
  `RacePredictor.Core.Tests/RacingPost/Examples/`, all dated **2026-05-20**:
  - `racecard_yarmouth_20260520_1910.html` — GB flat turf
  - `racecard_kempton_20260520_2000_headgear.html` — GB flat all-weather, headgear
  - `racecard_warwick_20260520_1700_hurdles.html` — GB jumps (hurdles)
  - `racecard_gowran_park_20260520_1820_unrated.html` — IRE, unrated
  - `racecard_happyvalley_20260520_1140.html` — HK
- *Supplement (live, issue 002 — TBD)* — two fresh live GB pulls (one flat handicap, one jumps)
  via `RacePredictor.Core/RacingPost/PuppeteerHtmlLoader.cs` (plain HTTP is 429-blocked per
  `AGENTS.md`). Pull dates and meeting/race types to be recorded here by issue 002. These are
  needed because the soft fields may be **members-only or absent** from the public DOM — and a
  thin midweek fixture could give a false "not available".

**Backfill presence-check (method).** "Backfill-able?" asks whether a candidate field *also*
appears on daily **result** pages, so it could be backfilled into historic `Results` rather than
starving forward-only. This is a **lightweight presence-check** against the existing
`results_*.html` fixtures only — not a full result-parser audit. Notable: the result fixtures
(both the 2022 set and the 2026 set — e.g. `results_southwell_20260218_1655.html`,
`results_punchestown_20260428_919174.html`) use **legacy markup with no `__NEXT_DATA__` and no
`data-testid`**, so the check is a plain-text presence scan of the result HTML. Representative
counts in `results_southwell_20260218_1655.html` (2026, current result-page era):

| term | hits | reading |
|---|---|---|
| `owner` | 12 | owner **is** carried on result pages → owner is backfill-able |
| `sire` / `dam` | 0 / 0 | breeding **absent** from result pages → not backfill-able |
| `verdict` | 0 | RP verdict absent → not backfill-able |
| `wind op` | 0 | wind-surgery flag absent → not backfill-able |
| `spotlight` | 3 | nav/link references only — the pre-race spotlight prose is **not** on result pages |
| `headgear` | 4 | headgear **code** present (already captured); first-time *flag* not distinguished |
| `allowance` | 1 | weak — claim is implied by weight-carried; needs result-parser confirmation |
| `comment` | 24 | present, but these are **post-race** in-running comments, not the pre-race spotlight |
| `RPR` / `OR ` | 15 / 42 | present but **post-race** on results (leaky — see `data-pitfalls.md`) |

Any newly-found backfill-able field is recorded as **input to** the sibling `todo.md` item
*"Backfill form / days-since / prize money into historic Results"* (cross-reference added in
issue 003) — backfill is **not** implemented here.

## Draft candidate inventory

One row per ignored pre-race signal. **Field / source** and **Backfill-able?** are filled now
(offline, grounded in the fixtures above). **Availability** and **Coverage** are filled by issue
002 (`TBD-002`); **Leakage**, **Type & parse difficulty**, **Predictive rationale**, and
**Verdict** by issue 003 (`TBD-003`). The `<sup>` badges and every named soft field
(hot-trainer/jockey form, Spotlight, RP verdict, breeding, owner, headgear-change / wind-op,
jockey allowance) appear as explicit rows.

| # | Field / signal | Source (DOM hook · `__NEXT_DATA__` key · `<sup>`) | Backfill-able? (result fixtures) | Availability | Coverage | Leakage | Type & parse difficulty | Predictive rationale | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Owner (id + name) | `Link__OwnerSilk` href · `ownerId`/`ownerName` | **Yes** — owner appears on result pages (12× in Southwell 2026) | TBD-002 | TBD-002 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 2 | Breeding — sire | `sireName`/`sireCountry` (`__NEXT_DATA__`; sample `Time Test`/`GB`) | **No** — absent from result fixtures (0) | TBD-002 | TBD-002 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 3 | Breeding — dam | `damName` (`__NEXT_DATA__`) | **No** — absent from result fixtures (0) | TBD-002 | TBD-002 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 4 | Headgear first-time flag | `horseHeadGearFirstTime` (bool, `__NEXT_DATA__`) | **No** — headgear code present on results but first-time flag not distinguished | TBD-002 | TBD-002 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 5 | Gelding first-time flag | `geldingFirstTime` (bool, `__NEXT_DATA__`) | **No** — not on result pages | TBD-002 | TBD-002 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 6 | Wind-surgery flag (+ count) | `Container__WindSurgery` (`w` + `<sup>` count) · `windSurgery` | **No** — "wind op" absent from result fixtures (0) | TBD-002 | TBD-002 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 7 | Jockey allowance / claim (lbs) | `weightAllowanceLbs`/`extraWeightLbs` (`__NEXT_DATA__`) | **Likely (partial)** — weight-carried + "allowance" appear on result pages; needs result-parser confirm | TBD-002 | TBD-002 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 8 | Jockey first-time on horse | `jockeyFirstTime` (bool, `__NEXT_DATA__`) | **No** — not on result pages | TBD-002 | TBD-002 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 9 | Trainer form — "RTF" / win-rate | `trainerRtf` (`__NEXT_DATA__`) · trainer win-rate `<sup class="sc-25f6462b-9">` (e.g. `59%`) | **No** — current-form stat, not on result pages | TBD-002 | TBD-002 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 10 | Jockey/trainer booking-count badge | `<sup class="sc-25f6462b-7">` (small int) on `Link__Jockey`/`Link__Trainer` | **No** — derived meeting stat, not on result pages | TBD-002 | TBD-002 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 11 | New-trainer races count (recent yard switch) | `newTrainerRacesCount` (`__NEXT_DATA__`) | **No** — not on result pages | TBD-002 | TBD-002 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 12 | Country of origin | `countryOrigin` (`__NEXT_DATA__`) | **No** — not on result pages | TBD-002 | TBD-002 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 13 | Silks / racing colours (image) | `Image__SilkImage`/`Container__SilkImage` (owner silk svg) | **No** — silk svg keyed by owner; not a result-page field | TBD-002 | TBD-002 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 14 | RP Spotlight (per-runner analyst comment) | `Button__ActionButtonSpotlight` · `spotlight`/`spotlightLucky` (`__NEXT_DATA__`) | **No** — pre-race spotlight not on result pages (result `comment` is post-race in-running) | TBD-002 | TBD-002 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 15 | RP Verdict (race-level analyst verdict + selection) | `Container__Verdict` · race-level `verdict` (`__NEXT_DATA__`); byline + named selection (sample `BIG CYPRESS preferred…`) | **No** — absent from result fixtures (0) | TBD-002 | TBD-002 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 16 | Weather | `Container__Weather` | **No** — not on result fixtures | TBD-002 | TBD-002 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 17 | Race conditions / eligibility prose | `Container__RaceConditionsContent` (+ `Header__RaceDetails`, `Button__RaceConditionsToggle`) | **Maybe** — mostly static eligibility text; partly reconstructable | TBD-002 | TBD-002 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 18 | Advisory info (reserves / non-runner notes) | `Section__RaceDetailsBottomAdvisoryInformation` · `Link__RaceDetailsBottomAdvisoryHorse` | **No** — not on result fixtures | TBD-002 | TBD-002 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 19 | Live bookmaker odds | `Container__OddsSection` · `odds-button-*` · `oddsValue`/`oddsDesc` | **N/A — tracked separately** | n/a | n/a | see [`odds-capture.md`](odds-capture.md) | see odds-capture | see odds-capture | **Out of scope** — live-odds capture is `odds-capture.md` Phase 2, not a new card field |

**Notes on the soft set (for issues 002/003).**

- **"Hot-trainer / hot-jockey form flag"** as a dedicated flame/icon was **not found** in the
  card DOM. The concrete in-form signals that *do* exist are row 9 (`trainerRtf` + the trainer
  win-rate `<sup>` badge) and row 11 (`newTrainerRacesCount`). Issue 003 should resolve the
  PRD's "hot form flag" candidate against these, rather than a non-existent flag.
- Rows 2–12 are dominantly sourced from `__NEXT_DATA__` (structured), so their parse difficulty
  is expected to be low — but their **availability** (does the public/logged-out DOM still ship
  `__NEXT_DATA__`, or is part of it members-gated?) must be confirmed by the live pulls in 002,
  since these fixtures may have been captured under a particular session state.
- The pre-race **Spotlight** and **Verdict** *text* (rows 14, 15) are the highest-NLP-risk
  candidates; whether their prose is in the static `__NEXT_DATA__`/DOM or lazy-loaded on
  interaction is exactly what 002's live pull must settle.

## Appendix — raw ignored `data-testid` inventory

Reproducible from the 5 named card fixtures (`_20260520`): the union of all `data-testid` values
is **396**; the parsers consume the **19** below; the remaining **377** are ignored. Reproduce
with: `grep -oE 'data-testid="[^"]+"' racecard_*_20260520*.html | sed -E 's/.*"([^"]+)".*/\1/' |
sort -u`, then subtract the consumed set.

**Consumed by the parsers (19) — not candidates.**

`RaceCardRunnerParser`: `Container__RunnerRowDesktop`, `Link__Horse`, `Link__Jockey`,
`Link__Trainer`, `Container__RunnerNumber`, `Container__HorseInfo`, `Text__DaysSinceLastRun`,
`Container__RunnerRowFormFigures`, `Container__RunnerStats`, `Link__BettingForecastHorse`.
`RaceCardParser`: `Link__CourseHeaderName`, `Container__CourseDetails`, `Wrapper__StallsWrapper`,
`Text__RaceDetailsTitle`, `Text__RaceDetailsPrizeMoney`, `Container__CourseHeaderInfo`,
`Text__CourseHeaderTime`, `Container__RaceDetailsInfo`, `Link__Going`.

**Ignored — runner / race-relevant (the candidate-bearing hooks).** These are the ignored
`data-testid`s that carry race or runner data (their candidates are in the inventory above; the
rest are layout wrappers / mobile duplicates retained here for completeness):

- Owner & silks: `Link__OwnerSilk`, `Container__SilkAndTips`, `Container__SilkImage`,
  `Image__SilkImage`
- Jockey/trainer: `Container__JockeyTrainerInfo` (holds the discarded `<sup>` badges)
- Per-runner extras: `Container__WindSurgery`, `Container__OddsSection`,
  `Container__RunnerMobileStats`, `Row__RunnerRowSecondary`, `Row__RunnerRowMain`,
  `Row__RunnerRowMobileMain`, `Row__RunnerRowMobileBottom`, `Container__RunnerRowMobile`,
  `Container__RunnerRowActionsDesktop`, `Container__RunnerRowActionsMobile`,
  `Button__ActionButtonSpotlight`, `Button__ActionButtonForm`, `Button__RunnerRowMobileControls`
- Race-level: `Container__Verdict`, `Container__Weather`, `Container__RaceConditionsContent`,
  `Header__RaceDetails`, `Button__RaceConditionsToggle`, `Container__RaceDetailsBottom`,
  `Container__RaceDetailsContainer`, `Section__RaceDetailsBottomAdvisoryInformation`,
  `Link__RaceDetailsBottomAdvisoryHorse`, `Row__RaceDetails`, `Container__TabView`,
  `Container__Runners`, `Container__RunnersTable`, `Container__RunnersTableHeader`
- Bet-slip / selection (UI, not card data): `Container__HorseSelection__Silk`,
  `Container__HorseSelection__Details`, `Text__HorseSelection__HorseName`,
  `Text__HorseSelection__SaddleclothNumber`
- Card view-toggles (signal that more views exist): `RaceLevelControls__SecondaryOption__Spotlights`,
  `RaceLevelControls__SecondaryOption__Form`, `RaceLevelControls__PrimaryTab__betting-odds`,
  `RaceLevelControls__PrimaryTab__newspaper-form-plus`, `RaceLevelControls__PrimaryTab__stats-plus`
- Dynamic per-runner id families (not stable hooks): `odds-button-<raceId>-<horseId>`,
  `Container__HorseSelection__<horseId>`

**Ignored — page chrome (not candidates).** The remaining ignored hooks are site furniture,
identical across all 5 fixtures: top/main/secondary navigation and hamburger/side drawer
(`Container__MainNavigation*`, `Container__SideDrawer*`, `*__DrawerItem`, `Link__MainMenu__*`,
`Link__Drawer*`, `SwiperSlide__SecondaryNav*`), footer & compliance
(`Container__Footer*`, `*FooterCompliance*`, `Link__TermsConditionsPolicies`, social
`Icon__*`/`Link__*` for Facebook/X/Instagram/etc.), responsible-gambling block
(`Container__GambleAware`, `*GamblersAnonymous*`, `*Gamstop*`, `*GamblingTherapy*`,
`Container__Raig`), bookmaker offers & logos (`*BookmakerOffer*`, `Logo__Bookmaker`,
`Icon__BookmakerOfferItemLogo__*`), ads (`Container__Ad`, `Container__AdPlaceholder`,
`Container__AdsContainer`), search/app-promo/cookie (`Container__SearchBar`, `Input__SearchInput`,
`Container__AppPromo`, `Container__CookieCompliance`), and date-strip / next-race navigation
(`ListItem__*`, `Link__Today`/`Link__Tomorrow`/`Link__<day>`, `Container__NextRaceNavigator`).
None carries race or runner data.
