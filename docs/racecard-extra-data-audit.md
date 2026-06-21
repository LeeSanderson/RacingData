# Racecard extra-data audit

> **Status: in progress.** This document is the deliverable of the research-only PRD
> *"Audit extra data available on Racing Post today's race cards"* (`issues/prd.md`). It is
> built in three passes:
> - **Issue 001 (this pass — offline foundation):** the Method note, the raw ignored-`data-testid`
>   appendix, and the *draft candidate inventory* with the columns derivable offline (field /
>   source, backfill-able?). The judgement columns carry explicit stubs.
> - **Issue 002 (live evidence — done):** filled **Availability** and **Coverage** from two fresh
>   logged-out live pulls (Brighton flat handicap + Hexham jumps, 2026-06-21) plus the fixtures;
>   confirmed `__NEXT_DATA__` and the structured soft set ship in the public DOM. `TBD-002` cleared.
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
- *Supplement (live, issue 002)* — two fresh **logged-out** GB pulls taken **2026-06-21** via
  `RacePredictor.Core/RacingPost/PuppeteerHtmlLoader.cs` (plain HTTP is 429-blocked per
  `AGENTS.md`; the loader emulates an iPad and runs no login), through a throwaway harness that
  reuses the loader:
  - **Flat handicap** — Brighton, race `921242`, *"Flat Turf, Handicap, Class 5"* (GB),
    `https://www.racingpost.com/racecards/7/brighton/2026-06-21/921242/`
  - **Jumps** — Hexham, race `921033`, *"Chase Turf, Handicap, Class 4"* (GB summer NH),
    `https://www.racingpost.com/racecards/25/hexham/2026-06-21/921033/`
  - *(supplementary)* a third pull — Brighton race `921240`, *"Flat Turf, Maiden, Class 4"* — was
    taken to separate "field absent from the card" from "signal merely didn't fire in this race".

  The live pulls were needed because the soft fields could have been **members-only or absent**
  from the public DOM. **Headline result: they are not.** Both logged-out pulls embed
  `__NEXT_DATA__`, and the entire structured per-runner soft set (owner / breeding / headgear &
  gelding first-time / wind-surgery / jockey allowance & first-time / `trainerRtf` /
  `newTrainerRacesCount` / `countryOrigin` / **`spotlight` prose**) is present per runner in the
  logged-out JSON — see the live-pull findings folded into the inventory's Availability/Coverage
  columns and the soft-set notes below. The network was reachable and headless Puppeteer
  succeeded, so the AFK fixture-only fallback was **not** needed.

  *Reproducibility / retention.* The three pulled HTML files are retained in the session
  scratchpad rather than committed (third-party card HTML, ~0.45 MB each, and today's race URLs
  are transient) — the durable record is the URLs + date + race types above plus the
  count-matrix method, all re-runnable against the loader. Two brittleness caveats surfaced:
  (1) the `<sup>` badge classes `sc-25f6462b-7`/`-9` are build-generated styled-component hashes —
  they happened to be **stable** across 2026-05-20 → 2026-06-21, but a future RP build can rotate
  them; (2) the live odds section only renders when a market is open at capture time (present on
  the Brighton handicap pull, absent on Hexham) — consistent with `odds-capture.md`.

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

One row per ignored pre-race signal. **Field / source** and **Backfill-able?** are offline
columns (grounded in the fixtures above). **Availability** and **Coverage** are now filled by
issue 002 (logged-out live pulls + the 5 fixtures); **Leakage**, **Type & parse difficulty**,
**Predictive rationale**, and **Verdict** remain for issue 003 (`TBD-003`). The `<sup>` badges and every named soft field
(hot-trainer/jockey form, Spotlight, RP verdict, breeding, owner, headgear-change / wind-op,
jockey allowance) appear as explicit rows.

| # | Field / signal | Source (DOM hook · `__NEXT_DATA__` key · `<sup>`) | Backfill-able? (result fixtures) | Availability | Coverage | Leakage | Type & parse difficulty | Predictive rationale | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Owner (id + name) | `Link__OwnerSilk` href · `ownerId`/`ownerName` | **Yes** — owner appears on result pages (12× in Southwell 2026) | Public DOM — `ownerName` + `Link__OwnerSilk` per runner, both live pulls | Universal — per-runner on all 8 cards (flat/jumps/IRE/HK) | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 2 | Breeding — sire | `sireName`/`sireCountry` (`__NEXT_DATA__`; sample `Time Test`/`GB`) | **No** — absent from result fixtures (0) | Public DOM — `sireName`/`sireCountry` per runner, both live pulls | Universal — all 8 cards incl HK | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 3 | Breeding — dam | `damName` (`__NEXT_DATA__`) | **No** — absent from result fixtures (0) | Public DOM — `damName` per runner, both live pulls | Universal — all 8 cards incl HK | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 4 | Headgear first-time flag | `horseHeadGearFirstTime` (bool, `__NEXT_DATA__`) | **No** — headgear code present on results but first-time flag not distinguished | Public DOM — `horseHeadGearFirstTime` bool per runner, both live pulls | Field universal (all 8); fires only when headgear is first-time (sparse) | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 5 | Gelding first-time flag | `geldingFirstTime` (bool, `__NEXT_DATA__`) | **No** — not on result pages | Public DOM — `geldingFirstTime` bool per runner, both live pulls | Field universal; `true` **rare** — 0 in both live pulls + 4/5 fixtures; 2 trues on Gowran (IRE) | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 6 | Wind-surgery flag (+ count) | `Container__WindSurgery` (`w` + `<sup>` count) · `windSurgery` | **No** — "wind op" absent from result fixtures (0) | Public DOM — `Container__WindSurgery` + `windSurgery` confirmed on live Hexham; JSON key per runner on all cards | Field universal; flag fires mainly on **jumps** (Hexham live, Warwick) + occasional flat (Brighton maiden); 0 on Yarmouth/Kempton/Gowran/HK | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 7 | Jockey allowance / claim (lbs) | `weightAllowanceLbs`/`extraWeightLbs` (`__NEXT_DATA__`) | **Likely (partial)** — weight-carried + "allowance" appear on result pages; needs result-parser confirm | Public DOM — `weightAllowanceLbs` per runner; non-zero claims on live Brighton hcap (5, 7 lb) & Hexham | Field universal (flat/jumps/IRE/HK); non-zero only for claimers → sparse, race-dependent (0 in maiden/Yarmouth/Kempton) | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 8 | Jockey first-time on horse | `jockeyFirstTime` (bool, `__NEXT_DATA__`) | **No** — not on result pages | Public DOM — `jockeyFirstTime` bool per runner; trues in live pulls | Field universal; fires across all types | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 9 | Trainer form — "RTF" / win-rate | `trainerRtf` (`__NEXT_DATA__`) · trainer win-rate `<sup class="sc-25f6462b-9">` (e.g. `59%`) | **No** — current-form stat, not on result pages | Public DOM — `trainerRtf` per runner (sample 54/53/43/null/29) + win-rate `<sup>` in both live pulls | `trainerRtf` universal (all 8); win-rate `<sup>` present GB/IRE but **absent on HK** | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 10 | Jockey/trainer booking-count badge | `<sup class="sc-25f6462b-7">` (small int) on `Link__Jockey`/`Link__Trainer` | **No** — derived meeting stat, not on result pages | Public DOM — booking-count `<sup>` in both live pulls | Universal incl HK (all 8); class hash brittle (see Method) | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 11 | New-trainer races count (recent yard switch) | `newTrainerRacesCount` (`__NEXT_DATA__`) | **No** — not on result pages | Public DOM — `newTrainerRacesCount` per runner; non-zero on live Brighton (2) & Hexham | Field universal; non-zero **rare** (recent yard switch) — 0–2 per card | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 12 | Country of origin | `countryOrigin` (`__NEXT_DATA__`) | **No** — not on result pages | Public DOM — `countryOrigin` per runner (sample "GB"/"IRE") | Universal — all 8 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 13 | Silks / racing colours (image) | `Image__SilkImage`/`Container__SilkImage` (owner silk svg) | **No** — silk svg keyed by owner; not a result-page field | Public DOM — `Image__SilkImage` present everywhere | Universal — all 8 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 14 | RP Spotlight (per-runner analyst comment) | `Button__ActionButtonSpotlight` · `spotlight`/`spotlightLucky` (`__NEXT_DATA__`) | **No** — pre-race spotlight not on result pages (result `comment` is post-race in-running) | **Public DOM, NOT members-only** — `spotlight` carries full per-runner prose in both logged-out pulls (sample in notes) | Universal — `spotlight` non-null per runner on all 8 incl HK | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 15 | RP Verdict (race-level analyst verdict + selection) | `Container__Verdict` (rendered prose + named selection, sample `PENTONVILLE…`); `__NEXT_DATA__` `verdict` key is **null** | **No** — absent from result fixtures (0) | Public DOM **as rendered `Container__Verdict` text**, not JSON (`verdict` key null in all 8) | **Partial** — present Brighton (hcap+maiden, live), Gowran (IRE), HK; **absent on live Hexham** + Yarmouth/Kempton/Warwick. Per-race, not a flat/jumps split | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 16 | Weather | `Container__Weather` | **No** — not on result fixtures | Public DOM — `Container__Weather` in both live pulls | GB/IRE present; **absent on HK** (Happy Valley) | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 17 | Race conditions / eligibility prose | `Container__RaceConditionsContent` (+ `Header__RaceDetails`, `Button__RaceConditionsToggle`) | **Maybe** — mostly static eligibility text; partly reconstructable | Public DOM — `Container__RaceConditionsContent` everywhere | Universal — all 8 | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 18 | Advisory info (reserves / non-runner notes) | `Section__RaceDetailsBottomAdvisoryInformation` · `Link__RaceDetailsBottomAdvisoryHorse` | **No** — not on result fixtures | Public DOM where rendered | **Rare** — only HK fixture; absent from all GB/IRE incl both live pulls (conditional: reserves/NR notes) | TBD-003 | TBD-003 | TBD-003 | TBD-003 |
| 19 | Live bookmaker odds | `Container__OddsSection` · `odds-button-*` · `oddsValue`/`oddsDesc` | **N/A — tracked separately** | n/a | n/a | see [`odds-capture.md`](odds-capture.md) | see odds-capture | see odds-capture | **Out of scope** — live-odds capture is `odds-capture.md` Phase 2, not a new card field |

**Notes on the soft set (live-pull findings, issue 002 — for 003).**

- **`__NEXT_DATA__` availability — RESOLVED.** Both **logged-out** live pulls (Brighton handicap,
  Hexham jumps) embed `__NEXT_DATA__`, and the full structured per-runner soft set is present in
  it (owner, breeding, headgear/gelding first-time, wind-surgery, jockey allowance & first-time,
  `trainerRtf`, `newTrainerRacesCount`, `countryOrigin`). The fixtures were **not** captured
  under a privileged session — none of the structured candidates is members-gated. So for rows
  1–14 the parse path really is "read a JSON property", which 003 should weight as low difficulty.
- **Spotlight — RESOLVED, public.** The per-runner `spotlight` value is full analyst prose in the
  logged-out JSON, e.g. *"In cheekpieces the last twice; pushed the long odds-on favourite close
  on his handicap debut (1m2f, good to firm) and then won as he liked at Wolverhampton on Tuesday
  … this 295,000gns yearling could easily rate much higher."* It is **not** members-only and is a
  JSON read, not a DOM/NLP scrape — though it is free text, so any *feature* extraction (vs raw
  capture) is still an NLP problem for the follow-on PRD.
- **Verdict — RESOLVED, but a correction to issue 001.** The race-level RP Verdict prose is in the
  **rendered `Container__Verdict` DOM** (e.g. *"VERDICT by Alistair Jones … PENTONVILLE looks
  well-in under a penalty for his AW win on Tuesday"* + a named selection via
  `Container__HorseSelection__<horseId>`), **not** a `__NEXT_DATA__` JSON property — the `verdict`
  JSON key is **null in all 5 fixtures and both live pulls**. So issue 001's "race-level `verdict`
  key in `__NEXT_DATA__`" was imprecise; capturing the Verdict means DOM scraping plus light NLP
  to pull the named selection, **not** a cheap JSON read. It is also **not on every card** (absent
  from the live Hexham jumps card and 3/5 fixtures) — 003 should weight both the higher parse cost
  and the patchy coverage.
- **"Hot-trainer / hot-jockey form flag"** as a dedicated flame/icon is **not found** in the card
  DOM (confirmed again live). The concrete in-form signals that *do* exist and are **public** are
  row 9 (`trainerRtf` + the trainer win-rate `<sup>` badge) and row 11 (`newTrainerRacesCount`).
  Note the win-rate `<sup>` badge is **absent on the HK (Happy Valley) card** while present on
  GB/IRE; 003 should resolve the PRD's "hot form flag" candidate against these, not a non-existent
  flag.
- **Coverage gaps worth carrying into 003's ranking:** the HK card lacks the trainer win-rate
  `<sup>` (row 9), `Container__Weather` (row 16), and the verdict is patchy (row 15); wind-surgery
  (row 6) skews jumps; several booleans (gelding/headgear first-time, new-trainer count) are
  *present everywhere as fields* but fire only sparsely, so their effective signal density is low.

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
