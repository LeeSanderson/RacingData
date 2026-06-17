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

## Pitfall 2 — a forecast price now sits on the card; it must not become a feature

**This pitfall changed shape.** It used to read "odds are unavailable at prediction
time" — `TodaysRaceCards.csv` carried the literal `"SP"` placeholder. That is no
longer true: the card now carries a real **betting-forecast** price (the RP morning
"tissue") for every runner at download, so `FractionalOdds`/`DecimalOdds` on the card
are a genuine pre-race price. See [`docs/odds-capture.md`](odds-capture.md).

That makes this the *more* dangerous pitfall now, not the safer one: a real price
exists **at prediction time**, so it *could* be fed to the model — and must not be.

- The Python predictor currently ignores card odds, so **no leakage occurs today**.
  This must stay true. The forecast must not silently become a model input or a
  selection/filter signal unless deliberately and safely introduced (and re-evaluated
  for the favourite-strength / odds-entropy traps that motivated this rule).
- The post-race **SP** (`FractionalOdds`/`DecimalOdds` in `Results_*.csv`) is still
  post-race, and the new `Forecast*` columns there are a *retrospective* record of the
  morning price. Both remain ROI/accuracy *measurement* constructs in `evaluate.py`,
  not signals the model conditions on.
- The **live / market** price (value betting, model-vs-market blends) is still
  genuinely unavailable early — that is Phase 2, not yet captured (see
  `docs/odds-capture.md`). So market-overlay strategies remain undeployable for now.

**The rule (unchanged, now load-bearing):** never use odds — forecast, live, or SP,
or anything derived from them — as a model input or a selection/filter signal. The
fact that a column is now *populated* at download is not permission to use it.

## The shared lesson

These pitfalls are two faces of the same discipline. Pitfall 1 is "looks available
but isn't" — a populated column (RPR/TSR) that secretly encodes the result. Pitfall 2
is now the opposite shape — a column (the card forecast) that genuinely *is* available
pre-race but still must not be used. So a new feature has to clear **two** bars, not
one:

1. *Was this value knowable, for this horse, before this race went off?* If not — or
   if you can't confirm the column is populated in the card at download time — it
   cannot be a feature.
2. Even if it passes (1), is feeding it deliberate and safe? Odds clear bar 1 now but
   are barred at bar 2 by the rule above. **Populated ≠ permitted.**
