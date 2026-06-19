# Advisory Staking — Strategy & Honesty Caveats

How the advisory `Stake` column in `Data/TodaysPredictions.csv` is produced, the knobs
that shape it, and — the point of this doc — what it does **not** yet prove. For the
leakage rule that governs how prices may reach a model, see
[`docs/data-pitfalls.md`](data-pitfalls.md) — Pitfall 2; for how the prices themselves are
captured, [`docs/odds-capture.md`](odds-capture.md). The governing caveat:

> **The stake is advisory and the backtest is a mechanics check, not a profit claim.**
> The number is read by a human who places bets by hand — nothing is automated, no
> real-money loop exists, and the historical figures are computed on a post-race **SP
> placeholder**, not the morning forecast the predict step actually serves on.

## The strategy

**Fractional Kelly behind a value gate** — `race_analytics/betting/staking.py`, a pure,
dependency-free module (no I/O, no pipeline coupling) so the math is unit-tested in
isolation. The predict step (`race_analytics/scripts/predict.py`) and the diagnostic
backtest (`race_analytics/scripts/backtest_staking.py`) both call it rather than
re-deriving anything.

One bet per covered race, on the model's top pick (the single `PredictedRank == 1`
runner — unchanged from today's published file). For that pick, over its **full field**:

- `ModelProb` — the model's `WinProbability` **normalized within the race** so the field
  sums to 1. Raw `WinProbability` is an un-normalized per-horse classifier output; the
  normalization is what makes it comparable to `MarketProb`. (This is why the stake is
  computed over the whole field before the file is filtered to the winner row — the
  published file only carries the one row, so the normalization has to happen upstream.)
- `p_market` = `MarketProb` — the per-race-normalized, **overround-removed** market-implied
  probability, from the sanctioned resolver (`race_analytics/features/market_prob.py`).
- `edge` = `ModelProb − p_market`.
- Gross decimal odds `O` = the resolved **forecast-when-present-else-SP** price; `b = O − 1`.
- Full Kelly fraction `f* = (ModelProb·O − 1) / (O − 1)`.

The stake is then:

- **`Stake = 0`** if `edge ≤ MIN_EDGE`, or `O` is missing / not greater than 1 (an
  unusable price never produces a garbage stake).
- otherwise **`Stake = min( KELLY_FRACTION · max(0, f*) · BANKROLL , CAP )`**, rounded to 2dp.

No-bet and no-value races are **retained** in the file with `Stake = 0`, never dropped, so
`TodaysPredictions.csv` stays a complete record of what was considered and what was skipped.

### The gross-pay / de-overround-judge split

A deliberate asymmetry: the Kelly **payout** term uses the gross price actually on offer
(`O`), while the **value judgement** uses the overround-removed `MarketProb`. Judging value
against the gross (margin-inflated) implied probability would make the bookmaker's
overround suppress genuine value bets; paying out at the de-overrounded fair price would
understate the real return on offer. Using each price for the term it belongs to avoids
double-counting the margin.

## The knobs and defaults

All are defaults in `staking.py`, overridable per call.

| Knob | Default | What it does |
|---|---|---|
| `KELLY_FRACTION` | **0.25** | Fraction of full Kelly staked. The primary risk / miscalibration buffer — turn down to start cautious, up with evidence. |
| `MIN_EDGE` | **0.03** | Minimum absolute edge (on normalized probability) to place any bet. Filters the near-zero noise edges an uncalibrated model produces. |
| `CAP` | **£5** | Maximum single stake, bounding short-priced high-confidence tails so one pick can't swallow a disproportionate share. |
| `BANKROLL` | **120** | Fixed notional scale (see below). |

`BANKROLL` is a **fixed, stateless notional scale — not a tracked balance.** There is no
running-balance accounting and no settlement feedback loop: the same bet always gets the
same stake regardless of the rest of the day's card or any prior result. Its only job is to
land the **median advised stake ≈ £1** — the bankroll-agnostic anchor of the design, which
lets a punter scale points to whatever real bankroll they use without the pipeline ever
needing to know it, and keeps the staked figures directly comparable to the flat-£1 ROI
methodology used throughout [`evaluations.md`](../evaluations.md). The value `120` was
derived from the diagnostic backtest's stake distribution (median £0.21 at the provisional
`BANKROLL = 25`; stake scales linearly below the cap, so `25 × (1 / 0.21) ≈ 119`, rounded
to 120 → median £1.02). Re-derive it if the stake distribution shifts.

## The caveats

These are the reason this doc exists. They travel with the feature the way the MarketProb
caveats do.

### 1. Probabilities are normalized but **not calibrated**

`ModelProb` is normalized within the race, but the underlying `WinProbability` is **not**
calibrated — no isotonic / Platt step maps the classifier's raw scores onto true
frequencies. Calibration is **deliberately deferred** (see "Out of Scope" in
[`issues/prd.md`](../issues/prd.md)). The **conservative Kelly fraction is the sole defence
against miscalibration**: betting a quarter of full Kelly keeps a systematically
over-confident probability from blowing up the notional bankroll. Treat the stake sizes as
*ordinally* sensible (bigger edge → bigger bet) rather than as optimal Kelly fractions.

### 2. The backtest is an **SP-placeholder / diagnostic-only** mechanics check

`backtest_staking.py` replays the production staking module over the saved walk-forward
evaluation results. It is flagged **diagnostic-only / no-promotion** in
[`evaluations.md`](../evaluations.md) (section "Staking diagnostic (Kelly + value gate)"),
exactly as the MarketProb A/B is. The reason is structural: forecast-odds capture is
forward-only and began ~2026-06, so the historical folds resolve `MarketProb` (the value
gate) and the settlement odds almost entirely from **post-race SP**, not the morning
forecast the predict step will actually serve on. This is the same eval/production
divergence documented in [`docs/data-pitfalls.md`](data-pitfalls.md) (Pitfall 2) that once
inflated a ratings model.

So the backtest confirms the staking *mechanics* and *relative* behaviour, **never a
forecast-time edge.** Concretely, on the active `GatedRecencyWeightedWinClassifier`'s 100
settleable picks: 18% coverage, flat-£1 ROI **−0.115**, Kelly-staked ROI **+0.331**. Do
**not** read that positive Kelly ROI as profitability — it is a small-sample artefact of
the value gate concentrating 18 bets on SP-defined edges that happened to land. The
flat-£1 figure is negative, in line with every full-coverage algorithm in the MarketProb
diagnostic. The staking diagnostic did **not** move `ACTIVE_ALGORITHM` — that documents the
prediction algorithm, not the staking strategy.

### 3. Not real-money validated — the **forward log** is what makes the rest measurable

Because the backtest can't speak to forecast-time profitability, the honest track record
accrues only **going forward**, on real forecast-priced days. The C# `validate` step
carries each pick's advised `Stake` through to the monthly `PredictionScores_YYYYMM.csv`
next to its outcome (the
`ValidateRaceCardPredictions/ValidateRaceCardPredictionsCommandHandler`), and logs a
**stake-weighted return** alongside the existing flat-£1 figure. As real forecast-priced
days accumulate, two things become possible that aren't today:

- a **calibration curve** computable from logged stakes-and-outcomes — so the deferred
  decision to calibrate the probabilities (caveat 1) can be **revisited with real data**,
  evidence-led rather than assumed;
- an **honest staked-ROI track record** on forecast prices, which is the only basis on
  which any staking claim should ever be made.

## The shared lesson

Same discipline as the leakage pitfalls: a number that *looks* validated isn't, until it's
been measured on the data production actually serves on. The staking math is sound and
tested; the *evidence that it makes money* is explicitly future work, gated on forecast
coverage. Until then the stake is advisory, the backtest is a mechanics check, and the
forward log is the thing quietly building the record that will one day let us say more.
