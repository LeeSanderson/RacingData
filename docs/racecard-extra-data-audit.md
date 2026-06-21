# Racecard extra-data audit

> **Status: complete.** This document is the deliverable of the research-only PRD
> *"Audit extra data available on Racing Post today's race cards"* (`issues/prd.md`). It was
> built in three passes (all now landed):
> - **Issue 001 (this pass — offline foundation):** the Method note, the raw ignored-`data-testid`
>   appendix, and the *draft candidate inventory* with the columns derivable offline (field /
>   source, backfill-able?). The judgement columns carry explicit stubs.
> - **Issue 002 (live evidence — done):** filled **Availability** and **Coverage** from two fresh
>   logged-out live pulls (Brighton flat handicap + Hexham jumps, 2026-06-21) plus the fixtures;
>   confirmed `__NEXT_DATA__` and the structured soft set ship in the public DOM. `TBD-002` cleared.
> - **Issue 003 (judgement — done):** filled **Leakage**, **Type & parse difficulty**, **Predictive
>   rationale**, and a go/no-go/defer **Verdict** for every candidate; added the ranked
>   [*Recommended to capture next*](#recommended-to-capture-next-shortlist) shortlist; linked the
>   doc from `todo.md`. `TBD-003` cleared.
>
> No production code is changed by any pass — this is reference, alongside
> [`odds-capture.md`](odds-capture.md) and [`data-pitfalls.md`](data-pitfalls.md).

## Recommended to capture next (shortlist)

Decision-ready output of the audit — a follow-on capture PRD can take this list directly. Ranked
by the PRD key: predictive plausibility × (availability × coverage), penalised by parse difficulty;
**leakage-suspect candidates capped at no-go** (none were — see below); **backfill-able fields jump
the queue** (usable immediately vs forward-only starvation). Full reasoning per candidate is in the
[inventory](#draft-candidate-inventory) Verdict column.

**Honest framing first.** The high-value structured pre-race signals (form figures, draw, weight,
age, headgear code, days-since, class, distance, prize, the `Card*` ratings) were already captured
by the prior PRD. The residual surface audited here is genuinely **soft / lower-signal**, and every
"go" below is a small, cheap increment — all but one is **forward-only** (card capture has no
archive, so each yields *zero* training rows until forward data accrues). The realistic near-term
win is modest; the single strongest item is trainer current form.

Ranked go-list (all are `__NEXT_DATA__` JSON reads from the per-runner object the scraper already
locates, so marginal parse cost is low):

1. **Trainer current form — `trainerRtf`** (row 9). Best plausibility × coverage at low cost; the
   "yard in form" angle. Universal, public, pre-race-safe — but a daily-recomputed rolling stat, so
   **freeze it at capture** (no historical reconstruction). Prefer the JSON over the brittle
   win-rate `<sup>`. *Forward-only.*
2. **First-time-flags bundle — `horseHeadGearFirstTime` + `geldingFirstTime` + `jockeyFirstTime`**
   (rows 4, 5, 8). Three per-runner bools from the same JSON object — capture together for ~one
   field's effort. High-signal-when-fires (first-time headgear, first-time-after-gelding), weak
   (jockey first-time); all fire sparsely. *Forward-only.*
3. **Breeding — `sireName`/`sireCountry`** (row 2), with `damName` (row 3) as a cheap add-on.
   Classic aptitude signal, strongest for lightly-raced/unexposed types where form is thin. JSON
   read, universal. *Forward-only.*
4. **Wind-surgery — `windSurgery`** (row 6). Recognised sharp-improvement angle, mainly NH; cheap
   but **sparse and jumps-skewed**, so value concentrates on jumps cards. *Forward-only.*
5. **Owner id — `ownerId`** (row 1). The **only backfill-able** candidate, so by the ranking key it
   jumps the queue on *immediacy*: capturing **and backfilling** it from result pages seeds future
   owner-strike-rate features without the forward-only starvation that handicaps 1–4. Low direct
   signal — treat it as a low-regret **enabler/identity key**, not a standalone feature. Feeds the
   sibling backlog item *"Backfill form / days-since / prize money into historic Results"* in
   [`../issues/todo.md`](../issues/todo.md).

**Deferred-but-attractive (revisit when a text/NLP pipeline exists):** the **RP Verdict**'s named
selection (row 15) is effectively a published tipster pick — a potentially strong meta-signal — but
it lives in the rendered DOM (not JSON), needs light NLP, and is patchy across cards; the per-runner
**Spotlight** prose (row 14) is public and cheap to *bank raw*, but turning it into a feature is an
NLP problem and it likely re-encodes already-captured ratings/form.

**Leakage finding (explicit).** Assessed against the `Card*`-vs-inherited-ratings standard in
[`data-pitfalls.md`](data-pitfalls.md): **no candidate is leakage-suspect.** All 18 are
morning-card facts knowable before the race, so none was capped at no-go on leakage grounds (the
no-gos below are on signal/cost grounds). The only nuances are *currency*, not leakage: trainer
form (row 9) is a moving stat that must be frozen at capture, and weather (row 16) is a capture-time
snapshot.

**Explicitly not recommended (no-go):** booking-count `<sup>` (row 10, low signal + brittle DOM;
`trainerRtf` is the better trainer-form source), silks image (row 13, needs computer vision; owner
id already captures identity), weather (row 16, marginal over the captured Going), race-conditions
prose (row 17, duplicates captured class/distance/prize), advisory info (row 18, operational not
predictive). **Deferred (cheap, low priority):** dam (row 3), jockey allowance (row 7), new-trainer
count (row 11), country of origin (row 12) — capture only as free add-ons to a "go" item.

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

The one newly-found backfill-able field is **owner** (row 1): it appears on result pages, so it
could be backfilled across history rather than starving forward-only. It is recorded as **input to**
the sibling `todo.md` item *"Backfill form / days-since / prize money into historic Results"* — a
cross-reference now sits in [`../issues/todo.md`](../issues/todo.md). Backfill is **not** implemented
here.

## Draft candidate inventory

One row per ignored pre-race signal. **Field / source** and **Backfill-able?** are offline columns
(grounded in the fixtures above); **Availability** and **Coverage** were filled by issue 002
(logged-out live pulls + the 5 fixtures); **Leakage**, **Type & parse difficulty**, **Predictive
rationale**, and the **Verdict** are filled by issue 003. The ranked go-list is in the
[shortlist](#recommended-to-capture-next-shortlist) above. The `<sup>` badges and every named soft field
(hot-trainer/jockey form, Spotlight, RP verdict, breeding, owner, headgear-change / wind-op,
jockey allowance) appear as explicit rows.

| # | Field / signal | Source (DOM hook · `__NEXT_DATA__` key · `<sup>`) | Backfill-able? (result fixtures) | Availability | Coverage | Leakage | Type & parse difficulty | Predictive rationale | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Owner (id + name) | `Link__OwnerSilk` href · `ownerId`/`ownerName` | **Yes** — owner appears on result pages (12× in Southwell 2026) | Public DOM — `ownerName` + `Link__OwnerSilk` per runner, both live pulls | Universal — per-runner on all 8 cards (flat/jumps/IRE/HK) | Clean — static pre-race identity | Low — `ownerId`/`ownerName` JSON read | Weak proxy for stable quality; only useful aggregated (owner strike-rate), largely re-encoded by ratings | **go (low-regret enabler)** — the **only backfill-able** field; capture `ownerId` to seed future owner-stats without forward-only starvation; not a standalone feature |
| 2 | Breeding — sire | `sireName`/`sireCountry` (`__NEXT_DATA__`; sample `Time Test`/`GB`) | **No** — absent from result fixtures (0) | Public DOM — `sireName`/`sireCountry` per runner, both live pulls | Universal — all 8 cards incl HK | Clean — pedigree is a static pre-race fact | Low — `sireName`/`sireCountry` JSON read | Sire biases progeny toward surface/going/distance aptitude; strong for lightly-raced types where form is thin | **go** — classic pre-race signal, cheap JSON, universal coverage |
| 3 | Breeding — dam | `damName` (`__NEXT_DATA__`) | **No** — absent from result fixtures (0) | Public DOM — `damName` per runner, both live pulls | Universal — all 8 cards incl HK | Clean — static | Low — `damName` JSON read | Damline adds aptitude signal; weaker/noisier than sire (higher cardinality, fewer progeny each) | **defer** — capture only as a cheap add-on to sire; low standalone signal |
| 4 | Headgear first-time flag | `horseHeadGearFirstTime` (bool, `__NEXT_DATA__`) | **No** — headgear code present on results but first-time flag not distinguished | Public DOM — `horseHeadGearFirstTime` bool per runner, both live pulls | Field universal (all 8); fires only when headgear is first-time (sparse) | Clean — headgear declared pre-race | Low — `horseHeadGearFirstTime` JSON bool | First-time blinkers/cheekpieces/hood often sharpen a disappointing horse; recognised positive angle | **go** — high-signal-when-fires, trivial bool; complements the static HeadGear already captured |
| 5 | Gelding first-time flag | `geldingFirstTime` (bool, `__NEXT_DATA__`) | **No** — not on result pages | Public DOM — `geldingFirstTime` bool per runner, both live pulls | Field universal; `true` **rare** — 0 in both live pulls + 4/5 fixtures; 2 trues on Gowran (IRE) | Clean — declared pre-race | Low — `geldingFirstTime` JSON bool (sibling of row 4) | First run after gelding can bring marked improvement (settles keen colts); classic but rare | **go (bundle)** — ~zero marginal cost beside row 4; strong when it fires though very rare |
| 6 | Wind-surgery flag (+ count) | `Container__WindSurgery` (`w` + `<sup>` count) · `windSurgery` | **No** — "wind op" absent from result fixtures (0) | Public DOM — `Container__WindSurgery` + `windSurgery` confirmed on live Hexham; JSON key per runner on all cards | Field universal; flag fires mainly on **jumps** (Hexham live, Warwick) + occasional flat (Brighton maiden); 0 on Yarmouth/Kempton/Gowran/HK | Clean — wind-op must be declared pre-race (BHA) | Low — `windSurgery` JSON (DOM `Container__WindSurgery` is a fallback) | First run after a wind op is a known sharp-improvement angle, mainly NH | **go (jumps-weighted)** — cheap, high-signal-when-fires; sparse and skews jumps |
| 7 | Jockey allowance / claim (lbs) | `weightAllowanceLbs`/`extraWeightLbs` (`__NEXT_DATA__`) | **Likely (partial)** — weight-carried + "allowance" appear on result pages; needs result-parser confirm | Public DOM — `weightAllowanceLbs` per runner; non-zero claims on live Brighton hcap (5, 7 lb) & Hexham | Field universal (flat/jumps/IRE/HK); non-zero only for claimers → sparse, race-dependent (0 in maiden/Yarmouth/Kempton) | Clean — claim known pre-race (may change on late jockey swaps) | Low — `weightAllowanceLbs`/`extraWeightLbs` JSON int | A claimer's allowance cuts weight but flags an inexperienced rider — net effect ambiguous; partly already in weight | **defer** — ambiguous sign, modest; revisit with weight/jockey interactions |
| 8 | Jockey first-time on horse | `jockeyFirstTime` (bool, `__NEXT_DATA__`) | **No** — not on result pages | Public DOM — `jockeyFirstTime` bool per runner; trues in live pulls | Field universal; fires across all types | Clean — booking known pre-race | Low — `jockeyFirstTime` JSON bool | New jockey/horse pairing; weak and directionally ambiguous (upgrade vs mere availability) | **defer (bundle)** — free add-on to the other first-time bools; low standalone signal |
| 9 | Trainer form — "RTF" / win-rate | `trainerRtf` (`__NEXT_DATA__`) · trainer win-rate `<sup class="sc-25f6462b-9">` (e.g. `59%`) | **No** — current-form stat, not on result pages | Public DOM — `trainerRtf` per runner (sample 54/53/43/null/29) + win-rate `<sup>` in both live pulls | `trainerRtf` universal (all 8); win-rate `<sup>` present GB/IRE but **absent on HK** | Clean pre-race rolling stat (excludes this race); **must be frozen at capture** — recomputed daily, no historical reconstruction (currency caveat, not leakage) | Low — `trainerRtf` JSON number; win-rate `<sup>` is a brittle duplicate (avoid) | "Yard in form" is a well-supported angle — hot trainers win at elevated rates | **go (top pick)** — best plausibility×coverage at low cost; use `trainerRtf` JSON, not the `<sup>` |
| 10 | Jockey/trainer booking-count badge | `<sup class="sc-25f6462b-7">` (small int) on `Link__Jockey`/`Link__Trainer` | **No** — derived meeting stat, not on result pages | Public DOM — booking-count `<sup>` in both live pulls | Universal incl HK (all 8); class hash brittle (see Method) | Clean — meeting-day count, pre-race | Low-med — DOM `<sup class="sc-25f6462b-7">`; brittle build-hash class | Count of a jockey/trainer's runners at the meeting; weak proxy for volume/confidence | **no-go** — low signal and brittle DOM; `trainerRtf` covers trainer form better |
| 11 | New-trainer races count (recent yard switch) | `newTrainerRacesCount` (`__NEXT_DATA__`) | **No** — not on result pages | Public DOM — `newTrainerRacesCount` per runner; non-zero on live Brighton (2) & Hexham | Field universal; non-zero **rare** (recent yard switch) — 0–2 per card | Clean — pre-race fact | Low — `newTrainerRacesCount` JSON int | Recent yard switch can trigger improvement ("first runs for a new trainer" angle) | **defer** — plausible but rare; revisit once core form features exist |
| 12 | Country of origin | `countryOrigin` (`__NEXT_DATA__`) | **No** — not on result pages | Public DOM — `countryOrigin` per runner (sample "GB"/"IRE") | Universal — all 8 | Clean — static | Low — `countryOrigin` JSON enum | Origin loosely proxies form-line class (imports); largely re-encoded by ratings | **defer** — weak; capture only if free alongside breeding |
| 13 | Silks / racing colours (image) | `Image__SilkImage`/`Container__SilkImage` (owner silk svg) | **No** — silk svg keyed by owner; not a result-page field | Public DOM — `Image__SilkImage` present everywhere | Universal — all 8 | Clean — static image | Capture URL Low, but a usable feature needs computer vision (High) | Identity/colours only — no predictive content beyond owner (row 1) | **no-go** — not a feature without vision; `ownerId` already captures the identity |
| 14 | RP Spotlight (per-runner analyst comment) | `Button__ActionButtonSpotlight` · `spotlight`/`spotlightLucky` (`__NEXT_DATA__`) | **No** — pre-race spotlight not on result pages (result `comment` is post-race in-running) | **Public DOM, NOT members-only** — `spotlight` carries full per-runner prose in both logged-out pulls (sample in notes) | Universal — `spotlight` non-null per runner on all 8 incl HK | Clean — analyst comment written pre-race | Capture Low (JSON string); **feature = High (NLP)** | Analyst synthesises form/fitness/suitability; potentially rich but likely re-encodes captured ratings/form | **defer** — no NLP pipeline today; cheap to bank raw text for later; revisit when text features are on the roadmap |
| 15 | RP Verdict (race-level analyst verdict + selection) | `Container__Verdict` (rendered prose + named selection, sample `PENTONVILLE…`); `__NEXT_DATA__` `verdict` key is **null** | **No** — absent from result fixtures (0) | Public DOM **as rendered `Container__Verdict` text**, not JSON (`verdict` key null in all 8) | **Partial** — present Brighton (hcap+maiden, live), Gowran (IRE), HK; **absent on live Hexham** + Yarmouth/Kempton/Warwick. Per-race, not a flat/jumps split | Clean — pre-race analyst verdict/selection | **Med-High** — DOM scrape (`Container__Verdict`) + light NLP for the named selection; not a JSON read; patchy coverage | The named selection is effectively a tipster pick — a potentially strong meta-signal; prose otherwise overlaps Spotlight | **defer** — attractive (tipster selection) but costly to parse and patchy across cards; revisit with an NLP/tips pipeline |
| 16 | Weather | `Container__Weather` | **No** — not on result fixtures | Public DOM — `Container__Weather` in both live pulls | GB/IRE present; **absent on HK** (Happy Valley) | Clean-ish — pre-race snapshot but updates toward off-time (capture-time dependent) | Low-med — short DOM string; needs normalising; absent on HK | Weather/going affect some horses, but Going is already captured; marginal residual | **no-go** — marginal over the captured Going; time-sensitive and HK-absent |
| 17 | Race conditions / eligibility prose | `Container__RaceConditionsContent` (+ `Header__RaceDetails`, `Button__RaceConditionsToggle`) | **Maybe** — mostly static eligibility text; partly reconstructable | Public DOM — `Container__RaceConditionsContent` everywhere | Universal — all 8 | Clean — static conditions | Med — prose parse; mostly eligibility boilerplate | Class/distance/prize already captured; residual eligibility text adds little lift | **no-go** — largely duplicates captured race attributes |
| 18 | Advisory info (reserves / non-runner notes) | `Section__RaceDetailsBottomAdvisoryInformation` · `Link__RaceDetailsBottomAdvisoryHorse` | **No** — not on result fixtures | Public DOM where rendered | **Rare** — only HK fixture; absent from all GB/IRE incl both live pulls (conditional: reserves/NR notes) | Clean — pre-race operational note | Low-med — prose; rare | Reserves/non-runner notes are operational, not predictive | **no-go** — operational metadata, no predictive content |
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
