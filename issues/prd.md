# PRD — Kelly-sized advisory stakes in `TodaysPredictions.csv`

## Problem Statement

`TodaysPredictions.csv` currently tells a punter *which* horse the model likes in each
covered race and how confident it is (`WinProbability`), but nothing about *how much to
stake*. Two horses with the same win probability are very different bets if one is 2.0 and
the other is 6.0; equally, a horse the model rates well above its market price is a better
bet than one the model merely agrees with. Today the punter has to eyeball all of this by
hand every morning. There is no single number that says "this race is worth more of your
money than that one," and no record of what a disciplined staking plan would have done.

## Solution

Add an advisory **`Stake`** column to `TodaysPredictions.csv`, produced by a **fractional
Kelly criterion with a value gate**. For each covered race's top pick the stake is derived
from the model's win probability and the runner's pre-race price: bet more when the model's
edge over the market is large, less when it is marginal, and nothing when the model does not
beat the market. The number is **advisory** — the punter reads it and places bets manually;
nothing is automated and no real-money loop exists. Alongside, a diagnostic backtest shows
what the staking plan would have done on historical folds (with explicit placeholder
caveats), and the forward prediction-scoring log is extended to capture the staked outcome
so a real, honest track record accrues over time.

## User Stories

1. As a punter using `TodaysPredictions.csv`, I want a `Stake` column next to each pick, so
   that I know how much to bet without re-deriving it by hand every morning.
2. As a punter, I want the stake to be larger when the model's edge over the market price is
   large, so that my money concentrates on the strongest opportunities.
3. As a punter, I want the stake to be smaller when the edge is marginal, so that I am not
   over-committing on near-coin-flip bets.
4. As a punter, I want a stake of zero when the model does not beat the market price, so that
   I skip races where I have no demonstrable edge.
5. As a punter, I want the typical stake to sit around a familiar £1 unit, so that the
   numbers are intuitive and I can scale them to whatever bankroll I actually use.
6. As a punter, I want a cap on the largest single stake, so that one short-priced
   high-confidence pick can't swallow a disproportionate share of my money.
7. As a punter, I want races where the model abstains or has no value to remain in the file
   with a zero stake rather than disappearing, so that the file is a complete record of what
   was considered and what was skipped.
8. As a punter, I want the staking aggressiveness to be a knob I can turn down (or up) as I
   gain confidence, so that I can start cautious and adjust with evidence.
9. As a risk-aware punter, I want the staking to use a conservative *fraction* of full
   Kelly, so that errors in the model's probabilities can't blow up my bankroll.
10. As a punter, I want the value judgement to compare the model against the market's *true*
    (overround-removed) probability, so that the bookmaker's margin doesn't make every bet
    look like poor value.
11. As a punter, I want the payout side of the stake calculation to use the actual gross
    price I'd be paid at, so that the stake reflects the real return on offer, not a
    theoretical fair price.
12. As a maintainer, I want the staking math isolated in a pure, dependency-free module, so
    that it can be unit-tested in isolation without running the whole pipeline.
13. As a maintainer, I want the prediction script to compute the stake from the full field's
    probabilities, so that the within-race normalization the value gate needs is actually
    possible (the published file only carries the winner row).
14. As a maintainer, I want no change to `run.ps1`'s step sequence, so that the daily run is
    unaffected and the stake is produced as part of the existing predict step.
15. As an analyst, I want a diagnostic backtest that replays the staking plan over the
    historical evaluation results, so that I can sanity-check the mechanics and compare
    Kelly-staked return against flat-£1 return.
16. As an analyst, I want that backtest to be clearly flagged as an SP-placeholder /
    diagnostic-only result, so that nobody mistakes it for evidence the strategy is
    profitable on real forecast prices.
17. As an analyst, I want the backtest to report the distribution of stakes it produces, so
    that the fixed scale constant can be tuned to land the typical bet near £1.
18. As an analyst, I want the forward prediction-scoring log to record the stake actually
    advised for each pick alongside its outcome, so that an honest staked-ROI track record
    accrues from real forecast-priced days onward.
19. As an analyst, I want the option of a stake-weighted return figure in the validate step's
    log output, so that the daily run reports staked performance, not just flat-£1
    performance.
20. As a future analyst, I want the logged stakes-and-outcomes to make a calibration curve
    computable later, so that the decision to calibrate the probabilities (deferred for now)
    can be revisited with real data.
21. As a maintainer, I want the staking strategy documented with its honesty caveats
    (uncalibrated probabilities, SP-placeholder backtest, not real-money validated), so that
    the limitations travel with the feature the way the MarketProb caveats do.
22. As a punter, I want stakes rounded to a sensible precision (pence), so that the advised
    number is directly placeable.
23. As a punter, I want a missing or unusable price to produce a zero stake rather than a
    garbage number, so that I'm never told to bet on a price the pipeline couldn't resolve.

## Implementation Decisions

### Staking strategy
- **Fractional Kelly with a value gate.** For each covered race's top pick (the single
  `PredictedRank == 1` runner; one bet per race, unchanged from today):
  - `ModelProb` = the model's `WinProbability` **normalized within the race** so the field
    sums to 1. Raw `WinProbability` is an un-normalized per-horse classifier output and is
    not directly comparable to `MarketProb`; normalization makes the two comparable.
  - `p_market` = `MarketProb` (already per-race normalized and overround-removed by the
    existing resolver).
  - `edge` = `ModelProb − p_market`.
  - Gross decimal odds `O` = the resolved forecast-when-present-else-SP price (the existing
    odds resolver); `b = O − 1`.
  - Full Kelly fraction `f* = (ModelProb·O − 1) / (O − 1)`.
  - If `edge ≤ MIN_EDGE`, or `O` is missing / not greater than 1 → **`Stake = 0`**.
  - Otherwise `Stake = min( KELLY_FRACTION · max(0, f*) · BANKROLL , CAP )`, rounded to 2dp.
- **Gross-pay / de-overround-judge split:** the payout term uses the gross price actually on
  offer (`O`), while the value judgement uses the overround-removed `MarketProb`. This avoids
  double-counting the bookmaker margin (which would otherwise suppress real value bets).
- **Probabilities are normalized but NOT calibrated.** Explicit probability calibration
  (isotonic/Platt) is deliberately deferred; the conservative Kelly fraction is the sole
  defence against miscalibration. The forward logging (below) is what makes calibration
  measurable later.

### Configuration knobs (all defaults tunable)
- `KELLY_FRACTION` — fraction of full Kelly to stake. Default **0.25**. The primary
  risk/miscalibration buffer.
- `MIN_EDGE` — minimum absolute edge (on normalized probability) required to place a bet.
  Default **~0.03**. Filters near-zero noise edges an uncalibrated model produces.
- `BANKROLL` (scale constant) — a **fixed, stateless** notional bankroll chosen so a typical
  bet lands near £1. No running-balance tracking and no settlement feedback loop; the same
  bet always gets the same stake regardless of the rest of the day's card. Its value is
  derived from the diagnostic backtest's stake distribution (set so the median stake ≈ £1).
- `CAP` — maximum single stake. Default **~£5**, to bound short-priced high-confidence tails.

### Modules built / modified
- **New pure staking module (a `betting` module under the Python package).** Pure,
  dependency-free functions: within-race probability normalization, the Kelly fraction, and
  the gated/capped stake sizing over a field frame. No I/O, no pipeline coupling — the deep,
  isolated, testable core of the feature.
- **`predict.py` (the predict step).** After the active algorithm produces the full field
  (`predict_field`), call the staking module on that full frame — where within-race
  normalization and the already-materialized `MarketProb` are available — then merge the
  resulting `Stake` onto the published winner rows. Add `Stake` to the output column set.
- **Diagnostic backtest (a new analysis script under the Python scripts).** Replays the same
  pure staking module over the saved walk-forward evaluation results (which already carry
  `WinProbability`, `MarketProb`, resolved odds, finishing position and field size). Reports
  Kelly-staked ROI vs flat-£1 ROI, coverage, and the stake distribution. Reuses the
  production staking functions so it also exercises them. Flagged SP-placeholder /
  diagnostic-only / no-promotion in the evaluation findings doc, consistent with the
  MarketProb eval discipline.
- **Forward logging (C# extraction stage, the validate command handler).** The handler reads
  `TodaysPredictions.csv` and writes the monthly prediction-scores file. Carry `Stake`
  through: add it to the prediction record read in and to the prediction-score record written
  out, so the staked advice is recorded next to each pick's outcome. Optionally make the
  handler's logged return figure stake-weighted (Σ stake·odds of winners − Σ stake of losers)
  rather than the current flat-£1 figure.

### Schema changes / contracts
- `TodaysPredictions.csv`: existing columns **plus `Stake`**. One row per covered race
  (unchanged). No-bet races are **retained** with `Stake = 0` (not dropped), so the file
  stays a complete record. Stakes rounded to 2dp.
- The monthly prediction-scores CSV gains a trailing `Stake` column. (Monthly results files
  are unchanged by this PRD.)

### Pipeline wiring
- **No change to `run.ps1`.** The stake is produced inside the existing predict step; the
  forward log is captured by the existing validate step. The step sequence is untouched.

## Testing Decisions

- **What makes a good test here:** test external behaviour, not implementation details. For
  the pure staking module, assert on stake values produced for hand-constructed fields with
  known probabilities and prices (positive edge → positive stake; edge below `MIN_EDGE` → 0;
  missing/≤1 odds → 0; cap enforced; within-race normalization makes probabilities sum to 1).
  For the C# handler, drive it via its `RunAsync`/command entry point and assert on the CSV
  it produces (a `Stake` column carried from input prediction to output score), exactly as
  the existing handler tests do — not on internal calls.
- **Modules to be tested:**
  - The pure Python staking module — full unit coverage (Kelly fraction, value gate, cap,
    normalization, missing-price handling). This is the deep module and the main correctness
    surface; tests live under the top-level `tests/` tree mirroring the package.
  - The diagnostic backtest — a thin behavioural test that it runs over a small fixture
    evaluation-results frame and produces the expected summary fields; the staking math
    itself is already covered by the pure-module tests it reuses.
  - The C# validate handler — extend the existing handler test to assert the `Stake` column
    rides from `TodaysPredictions.csv` through to the prediction-scores output.
- **Prior art:** `ValidateRaceCardPredictionsCommandHandlerShould` and
  `UpdateResultsCommandHandlerShould` for the C# handler style (drive via the command, assert
  on the written CSV); existing pytest modules under `tests/` for the pure-function style.
- **Python coverage note:** this repo does have pytest coverage under `tests/` (unlike many
  PRDs that touch the Python stage), so the pure staking module **will** get real unit tests
  rather than being verified only via `run.ps1` output. The end-to-end predict wiring is
  verified by running the predict step and inspecting `TodaysPredictions.csv`.

## Out of Scope

- **Probability calibration.** No isotonic/Platt calibration of `WinProbability` in this PRD;
  fractional Kelly is the buffer and the forward log makes calibration a *later, evidence-led*
  decision.
- **A live-market value-betting strategy.** Betting against a live/closing market price, or
  any model-vs-market overlay that needs a trustworthy live price, remains out of scope —
  that depends on Phase 2 live-odds capture (see `docs/odds-capture.md`) and a demonstrated
  forecast-time edge, neither of which exists yet. This PRD uses the morning **forecast**
  price only, and treats the stake as advisory.
- **Dynamic/compounding bankroll.** No running-balance tracking, no settlement feedback loop;
  the bankroll scale is a fixed notional constant.
- **Multiple bets per race / each-way / dutching.** One win bet per covered race, on the
  model's top pick, unchanged.
- **Promoting any strategy on the basis of the diagnostic backtest.** With ~0% real forecast
  coverage in history the backtest measures the SP placeholder; it is a mechanics check only.
- **Automated bet placement.** The stake is a number in a CSV the punter acts on by hand.

## Further Notes

- **Why the backtest can't validate profitability yet:** forecast-odds capture is
  forward-only and began ~2026-06, so the historical evaluation folds resolve `MarketProb`
  (and the resolved odds) almost entirely from post-race SP, not the morning forecast the
  predict step will actually serve on. This is the same eval/production divergence documented
  for MarketProb (`docs/data-pitfalls.md`, Pitfall 2). The diagnostic therefore confirms the
  staking *mechanics* and relative behaviour, never real-money edge. The honest track record
  comes only from the forward log on real forecast-priced days.
- **Relationship to the backlog:** this PRD scopes the `todo.md` item "Odds + confidence in
  TodaysPredictions.csv → bet sizing". The separate backlog item "Value-betting /
  market-overlay strategy" stays deferred (it needs Phase 2 live prices + a demonstrated
  edge) and is explicitly *not* what this PRD delivers.
- **The £1 anchor is deliberately bankroll-agnostic.** Expressing the typical bet as ~£1
  against a fixed notional lets the punter scale points to their real bankroll without the
  pipeline ever needing to know it, and keeps the staked figures directly comparable to the
  existing flat-£1 ROI methodology used throughout the evaluation findings.
- **Defaults assumed pending objection:** no-bet rows retained with `Stake = 0`; stakes
  rounded to 2dp; `KELLY_FRACTION = 0.25`, `MIN_EDGE ≈ 0.03`, `CAP ≈ £5`, with `BANKROLL`
  calibrated from the backtest stake distribution.
