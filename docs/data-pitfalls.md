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
(`extract_horse_stats` → `Horse_Stats.csv`) — **never** from the race-day card row.

## Pitfall 2 — market odds are unavailable at prediction time

`DecimalOdds` / `FractionalOdds` are **not populated when a racecard is downloaded**.
`Data/TodaysRaceCards.csv` has the columns, but they are empty at download time
(`FractionalOdds` is the literal string `"SP"`); the market forms closer to the off.
Starting-price odds appear only later, retrospectively, in `Results_*.csv`.

**Consequence:** any odds-dependent strategy is undeployable in production —
market-overlay / value betting, model-vs-market blends, and abstain filters keyed on
favourite strength or odds entropy all require a price that isn't known when the
prediction is made.

**The rule:** never use odds (or anything derived from them) as a model input or a
selection/filter signal. Odds are usable **only** to *measure* ROI/accuracy after the
fact in `evaluate.py`. The market-favourite baseline and the ROI metric are therefore
retrospective evaluation constructs, not signals the model conditions on.

## The shared lesson

Both pitfalls are the same "looks available but isn't" trap. When considering a new
feature, ask: *was this value knowable, for this horse, before this race went off?*
If not — or if you can't confirm the column is actually populated in the card at
download time — it cannot be a feature.
