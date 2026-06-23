# Prediction-Time Data Pitfalls

Two columns in the raw data *look* like useful model inputs but are not legitimately
available when a real prediction is made. Both have already produced badly inflated
or undeployable results once. The governing rule:

> **Only data knowable *before* a race may be a feature or a selection/filter.**
> Column presence in a card file is **not** proof the column is populated at download —
> verify population before treating any field as a feature.

## Pitfall 1 — `RacingPostRating` / `TopSpeedRating` are post-race figures (leakage)

`RacingPostRating` (RPR) and `TopSpeedRating` (TSR) in `Results_*.csv` are assigned
*after* the race as performance ratings — they encode the result.

- Within a race, their Spearman correlation vs finishing position is ≈ **−0.88 / −0.86**,
  and the top-rated horse wins ~**74% / 71%** of the time.
- `OfficialRating` (Spearman −0.11, top-rated wins 18.7%) is the only genuinely
  *pre-race* rating of the three.

**What went wrong:** a TSR-gated `RatingsXGBoostAlgorithm` once reported **0.78**
evaluation accuracy. Real production accuracy over 514 logged bets was **0.265** —
roughly 3× inflation. The eval was feeding each fold's *own* post-race ratings to the
model (near-oracle), while production cards carry only weak pre-race form. After the
leak was removed, the same algorithm scored **0.290** — in line with the 0.265 anchor,
and the 0.78 headline fully collapsed.

**The rule:** anything ratings-related must come from a horse's **previous** race
(`LastRace{Official,RacingPost,TopSpeed}Rating`, already leak-free in
`Race_Features.csv`), reaching algorithms only through the per-horse **stats join**
(`extract_horse_stats` → `Horse_Stats.csv`) — **never** the post-race result ratings.

**Pre-race card ratings are the exception — and they *are* safe.** The OR/RPR/TSR
shown on the *morning racecard* are genuine pre-race figures (the rating standing
before the race is run), unlike the result-page ratings above which are recomputed
after it. Those card ratings are now captured and written back into `Results_*.csv`
as the **`Card*`** columns — `CardOfficialRating`, `CardRacingPostRating`,
`CardTopSpeedRating` — kept deliberately distinct from the inherited
`OfficialRating`/`RacingPostRating`/`TopSpeedRating`, which retain their
**post-race, leaky** meaning in results. So the "never the result ratings" rule above
is about the *post-race* figures, not these pre-race `Card*` values: **`Card*` clears
bar 1 and may be used directly as a feature** once enough have accumulated; the
un-prefixed rating columns must not. (`Card*` is a clean *current-race* pre-race
rating source, alongside the previous-race `LastRace*` values from the stats join.)

Two caveats apply to the `Card*` columns and the other newly-captured pre-race fields
(`DaysSinceLastRun`, `FormFigures`, `PrizeMoney`/`PrizeMoneyValue`, and the
owner/breeding/extras fields — `OwnerId`/`OwnerName`, `SireName`/`SireCountry`/`DamName`,
the first-time flags, `WindSurgery`, `TrainerRtf`, `JockeyAllowanceLbs`,
`NewTrainerRacesCount`, `CountryOfOrigin`, `Spotlight` — all now forwarded by the
write-back too):

- **Forward-only coverage.** They populate from *deployment forward* via the
  card→result write-back (see [`docs/odds-capture.md`](odds-capture.md)); coverage
  starts at the deployment date and **historical rows are blank by design** (no
  racecard backfill). Treat them as features only once accumulated coverage is
  sufficient — a model trained across the blank history would see them as
  mostly-missing.
- **Prize money is not currency-normalised.** `PrizeMoneyValue` is the raw figure with
  the currency symbol and thousands separators stripped; the displayed currency is
  **not** converted across countries, so a £-card and a €-card yield numbers on
  different scales. The raw `PrizeMoney` string preserves the original symbol for any
  later normalisation.

## Pitfall 2 — odds enter the model *only* through the sanctioned `MarketProb` resolver

**This pitfall changed shape twice.** It first read "odds are unavailable at prediction
time" — `TodaysRaceCards.csv` carried the literal `"SP"` placeholder. That stopped
being true when the card gained a real **betting-forecast** price (the RP morning
"tissue") for every runner at download, so `FractionalOdds`/`DecimalOdds` on the card
are a genuine pre-race price (see [`docs/odds-capture.md`](odds-capture.md)). For a
while the rule then read "a real price exists at prediction time, so it *could* be fed
to the model — and must not be."

**That blanket ban has now been consciously and narrowly relaxed.** The market-prob
work introduced **`MarketProb`** — the per-race-normalized, market-implied win
probability — as a **deliberately sanctioned** model feature. It is the *only* channel
through which odds may reach a model, and it enters behind a single resolver
(`race_analytics/features/market_prob.py`):

- `MarketProb` resolves each runner's price **forecast-when-present-else-SP**, converts
  it to an implied probability, and normalizes within each race so the field sums to 1.
  The forecast clears bar 1 (knowable before the off) and the PRD consciously clears
  bar 2 (introduced deliberately, behind a resolver, with honest evaluation and
  deferred adoption) — so `MarketProb` is a permitted feature.
- The **SP fallback is a transitional placeholder, not a sanctioned feature.** With
  near-zero forecast coverage in history, `MarketProb` is today mostly computed from the
  post-race SP, so the current eval reads an SP placeholder, not the forecast production
  will serve on — the same eval/production divergence that once inflated a ratings model
  (Pitfall 1). The mitigation is structural: no promotion is made off the SP-placeholder
  eval, which is flagged diagnostic in [`evaluations.md`](../evaluations.md). As forecast
  coverage accrues the fallback retires itself.
- The post-race **SP** (`FractionalOdds`/`DecimalOdds` in `Results_*.csv`) and the
  `Forecast*` results columns remain **barred as direct features** — SP because it is
  post-race, the `Forecast*` results columns because they are a *retrospective* record.
  They stay ROI/accuracy *measurement* constructs in `evaluate.py` (now valued through
  the same resolver, so model and measurement share one notion of "the market").
- The **live / market** price (value betting, model-vs-market blends) is still
  genuinely unavailable early — that is Phase 2, not yet captured (see
  `docs/odds-capture.md`). So market-overlay strategies remain undeployable for now.

**The rule (now precise):** the only odds-derived signal a model may condition on is
`MarketProb`, through its resolver. Raw card / SP / forecast prices — and anything else
derived from them — must never be a direct model input or a selection/filter signal.
Sanctioning `MarketProb` added **no** odds-presence race-selection gate; the predicted
population is unchanged. The fact that a column is *populated* at download is still not
blanket permission to use it — permission is granted feature by feature, deliberately.

## The shared lesson

These pitfalls are two faces of the same discipline. Pitfall 1 is "looks available
but isn't" — a populated column (RPR/TSR) that secretly encodes the result. Pitfall 2
is now the opposite shape — a column (the card forecast) that genuinely *is* available
pre-race but still must not be used. So a new feature has to clear **two** bars, not
one:

1. *Was this value knowable, for this horse, before this race went off?* If not — or
   if you can't confirm the column is populated in the card at download time — it
   cannot be a feature.
2. Even if it passes (1), is feeding it deliberate and safe? The forecast price clears
   bar 1 (it exists at download), and `MarketProb` is the one odds-derived signal that
   has consciously cleared bar 2 — introduced deliberately, behind a resolver, with
   honest evaluation and deferred adoption. Raw SP / forecast prices stay barred at bar
   2. **Populated ≠ permitted — permission is granted feature by feature.**
