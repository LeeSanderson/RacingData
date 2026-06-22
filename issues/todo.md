# Future Ideas & Backlog

This file is a **lightweight backlog of ideas and deferred work** — things worth remembering
but not yet scoped into a numbered issue. It is not a sprint board: nothing here has been
committed to or estimated. Items move into numbered issues (e.g. `010-...md`) only when they
are ready to be worked.

> **For agents:** read this file when the user asks what to do next, wants to explore
> future direction, or when the active issues/ queue is empty.

---

## Odds / Market signal

### Phase 2 — live in-running market odds capture
The `docs/odds-capture.md` roadmap describes this. The C# scraper currently captures only
the morning forecast price at download time. Capturing live / closing odds requires a
separate scrape pass after results are in. Nothing here is actionable until the forecast
coverage story from the MarketProb PRD (closed 2026-06-18) has had time to mature.

### ⏰ Re-evaluate MarketProb on honest forecast-fed data — RE-EVAL REMINDER (coverage-gated)
This is the durable re-eval reminder from `issues/009` (now closed). The reminder lives
here in the backlog rather than as a cloud cron because the trigger is a **data condition,
not a date** — agents read this file when the active `issues/` queue is empty.

**Trigger:** re-run the full MarketProb A/B once `ForecastDecimalOdds` coverage in the
7-month training window reaches **≥ 80%** of rows carrying a real forecast price (not the
SP fallback). Forecast capture is forward-only with no backfill and began ~2026-06, so an
≥80%-forecast 7-month window will not exist until ~Jan 2027. An optional ~1-month
checkpoint (~mid-Jul 2026) is still roughly six-sevenths SP — an informational-only early
read that **cannot** move `ACTIVE_ALGORITHM`.

**When it fires:** re-run the A/B across all registered algorithms on the forecast-fed
window and reconsider `ACTIVE_ALGORITHM` against the normal gate — net **ROI** plus
**early/late fold stability**, *not* accuracy alone. **Baseline to beat:** the 13-fold
SP-placeholder diagnostic in `evaluations.md` (section "13-fold MarketProb diagnostic —
2026-06-04 → 2026-06-16"). Read the *relative* picture: that diagnostic's accuracy lift is
favourite-tracking via the SP-defined `MarketProb`, and ROI is negative across every
full-coverage algorithm, so a genuine promotion needs a real forecast-time ROI edge.

### ⏰ Recheck forecast<->SP fidelity as coverage grows — RECHECK REMINDER
Run `python -m race_analytics.scripts.forecast_vs_sp` to compare the morning
`ForecastDecimalOdds` against the post-race SP (`DecimalOdds`) for runners where both
are present. This tells us how trustworthy forecast-derived `MarketProb` is, and feeds
the coverage-gated re-eval above.

**Baseline (2026-06-19, first populated day — 06/18, 45 races / 468 runners):**
strong *ordering* agreement (log-odds & implied-prob Pearson ~0.89, within-race rank
corr ~0.79, favourite match 62%) but loose *price* agreement (median runner ~33% off SP,
only ~13% within 10%); forecast is typically ~10% shorter than SP (median ratio 0.90).

**Recheck cadence** (forecast capture is forward-only, began ~2026-06, so the sample
grows daily):
- **~mid-Jul 2026** — first meaningful read once ~2-3 weeks of forecast-fed days exist;
  confirm the ~0.89 / 62% / 10%-shorter pattern holds beyond a single day.
- **Monthly thereafter** — watch for drift; a falling favourite-match or rank-corr would
  undermine forecast-derived `MarketProb` before the ≥80%-coverage re-eval even fires.
- Fold the latest figures back into this entry when re-run, so the baseline stays current.

---

## Model improvements

### Features from the newly-captured racecard fields — NEW (capture shipped 2026-06-22)
The forward-capture PRD (issues 001–005) now banks 14 pre-race card fields on `TodaysRaceCards.csv`
that no algorithm yet consumes: owner (`OwnerId`/`OwnerName`), breeding (`SireName`/`SireCountry`/
`DamName`), first-time flags (`HeadgearFirstTime`/`GeldingFirstTime`/`JockeyFirstTime`),
`WindSurgery`, `TrainerRtf`, `JockeyAllowanceLbs`, `NewTrainerRacesCount`, `CountryOfOrigin`, and
`Spotlight`. **Feature engineering was explicitly out of scope of the capture PRD** — deriving
model features from these columns is this follow-on. Candidate features: owner strike-rate,
sire/dam aptitude (for lightly-raced types whose form is thin), the first-time
headgear/gelding/wind-op angles, and a "yard in form" feature off `TrainerRtf` (a capture-time
snapshot, leak-free).
**Forward-only constraint:** capture began ~2026-06 with no archive/backfill, so every field yields
*zero* training rows until forward history accrues, and several fire sparsely (gelding-first-time,
wind-surgery, new-trainer count). A useful modelling window is months out — assess per-field coverage
before scoping any feature.

### NLP over the banked Spotlight corpus + capture RP Verdict — DEFERRED (corpus now accruing)
Issue 005 banks the per-runner `Spotlight` analyst prose **verbatim** (raw, no parsing) on
`TodaysRaceCards.csv`, so a forward text corpus is now accruing daily. A future text/NLP pipeline
could mine it for sentiment / named-selection / pace signals — still genuinely deferred, no NLP
work scoped. The race-level **RP Verdict** remains **uncaptured** (it is rendered DOM, not in
`__NEXT_DATA__`, needs light NLP for the named selection, and is patchy across cards — explicitly
out of scope of the capture PRD); capturing it belongs in this same future text PRD.

### Value-betting / market-overlay strategy
Bet only when model win-probability exceeds market-implied probability; stake by edge.
Pre-requisite: a trustworthy live price (Phase 2 above) and a model with a demonstrated
edge over the market. Out of scope until both conditions hold.

### Trainer stats coverage
Trainer stats exist in the pipeline but aren't yet wired into every algorithm
(`trainer_stats=None` is the current default). Explore whether adding trainer features
improves accuracy — but check for sample-size issues (new trainers in walk-forward folds).

### Ensemble / stacking experiments
Combine the outputs of multiple registered algorithms (e.g. recency-weighted classifier +
Ridge regressor) via a meta-learner. Likely needs more walk-forward history before the
signal-to-noise ratio is useful.

---

## Data sourcing & scraping

### Research extra data available on Racing Post today's race cards — ✅ RESEARCHED (2026-06-21)
Audited and written up in **[`../docs/racecard-extra-data-audit.md`](../docs/racecard-extra-data-audit.md)**
(durable findings doc, alongside `odds-capture.md` / `data-pitfalls.md`). The audit diffed the
card `data-testid` inventory against the parsers, decoded the discarded `<sup>` badges, and — the
key finding — established that a `__NEXT_DATA__` JSON island (present in the **public/logged-out**
DOM, confirmed by live Brighton-flat + Hexham-jumps pulls) carries structured per-runner versions
of nearly every soft field. 18 candidates were ranked with availability / coverage / leakage /
parse-difficulty / verdict; **no candidate is leakage-suspect** (all are morning-card pre-race
facts).
**Outcome — honest:** the high-value structured signals were already captured by the pre-race
racecard-data PRD, so the residual is soft/lower-signal and every recommendation is a small, mostly
forward-only increment. The `go` shortlist (copy-paste ready in the doc): trainer current form
(`trainerRtf`), a first-time-flags bundle (`horseHeadGearFirstTime`/`geldingFirstTime`/`jockeyFirstTime`),
breeding (`sireName`), wind-surgery (`windSurgery`), and **owner id**.
RP Verdict and Spotlight are **deferred** pending an NLP/text pipeline.
**Next step — ✅ CAPTURE SHIPPED (2026-06-22):** the follow-on capture PRD took the shortlist
directly and is now fully implemented (issues 001–005, commits `b705b12`..`baff799`). All 14
audited go + defer fields are forward-captured as new trailing columns on `TodaysRaceCards.csv`
via a `__NEXT_DATA__` JSON reader with throwing schema validation + a DOM cross-validation oracle.
Both this research item and the capture PRD are closed. **Data-shape correction the build found:**
the audit assumed `windSurgery` was a bool, but the live JSON carries it (and `trainerRtf`) as an
**integer** — both are captured faithfully as `int?` (see issue 005's completion note); the audit
doc still reads "bool" and should be corrected when next touched. The downstream **feature
engineering** the capture enables was out of scope of that PRD — see *Model improvements →
"Features from the newly-captured racecard fields"* below.

## Data quality & pipeline

### Backfill ForecastDecimalOdds into historic Results
The `validate` step that merges forecast prices into `Results_*.csv` is forward-only by
design. A one-time backfill pass using the Racing Post historical odds API (if available)
would increase MarketProb training coverage immediately. Non-trivial scraping work; assess
data availability first.

### Backfill form / days-since / prize money into historic Results
Sibling to the ForecastDecimalOdds backfill above. The same `validate` write-back also
lands `FormFigures`, `DaysSinceLastRun` and `PrizeMoney`/`PrizeMoneyValue`, and is
likewise forward-only, so historic result rows are blank. Unlike the ratings, these
three are **pre-race facts that may already appear on the daily-scraped result pages**,
so a single re-scrape of historic result pages could backfill them across all history —
no racecard archive needed. The `Card*` ratings are **deliberately excluded**: result
pages carry only the **post-race** OR/RPR/TSR, so there is no pre-race rating to recover
there (exactly why they must be captured from the card going forward). Assess whether the
result-page markup actually exposes form / days-since / prize before scoping.

### Going encoding robustness
`encode_going()` defaults missing `Going` to `"Good"`. Audit whether this is the most
common value in the data or just a safe placeholder — replace with the empirical mode if
they differ.

---

## Infrastructure

### CI timing — evaluate.py in CI
The walk-forward eval is too slow (~36-48 hours for 180 folds) to run in CI. A short-fold
smoke check (e.g. `--folds 3`) could catch regressions without full cost. Needs thought on
what assertions to make so it doesn't just pass vacuously.

### Python test coverage gaps
Tests live in `tests/` but coverage is thin outside the modules touched by recent PRDs.
No specific gaps tracked here — when working in an under-tested area, expand coverage as
you go rather than batch it.
