# Pure `betting` staking module + unit tests

## Parent PRD

`issues/prd.md` — sections "Staking strategy", "Configuration knobs", "Modules built / modified" (the new pure staking module), and "Testing Decisions".

## What to build

A new pure, dependency-free Python module under the package — `race_analytics/betting/` — that holds the staking math and nothing else (no I/O, no pipeline coupling). This is the deep, isolated, testable core of the feature; everything else in this PRD consumes it.

It exposes pure functions over a *field* frame (one row per runner, with `RaceId`, `WinProbability`, `MarketProb`, and a resolved decimal-odds column):

- **Within-race normalization** — turn the un-normalized per-horse `WinProbability` into `ModelProb` by normalizing within each `RaceId` so the field sums to 1 (makes it comparable to `MarketProb`).
- **Full Kelly fraction** — `f* = (ModelProb·O − 1) / (O − 1)` where `O` is the gross decimal odds.
- **Gated + capped stake sizing** — `edge = ModelProb − MarketProb`; if `edge ≤ MIN_EDGE` or `O` is missing / not `> 1` then `Stake = 0`; otherwise `Stake = min(KELLY_FRACTION · max(0, f*) · BANKROLL, CAP)`, rounded to 2dp.

The **gross-pay / de-overround-judge split** must hold: the payout term uses the gross price actually on offer (`O`), while the value gate uses the overround-removed `MarketProb`. Config knobs are parameters/constants with the PRD defaults: `KELLY_FRACTION = 0.25`, `MIN_EDGE ≈ 0.03`, `CAP ≈ £5`. `BANKROLL` ships as a **documented provisional placeholder here** and is finalized from the backtest distribution in `issues/005-calibrate-bankroll-and-eval-diagnostic.md`.

## Acceptance criteria

- [ ] New module under `race_analytics/betting/` exposes pure functions for within-race normalization, the Kelly fraction, and gated/capped stake sizing over a field DataFrame (returns a `Stake` per row).
- [ ] Positive-edge pick with sound odds → positive stake; `edge ≤ MIN_EDGE` → `Stake = 0`; missing or `≤ 1` odds → `Stake = 0`; the `CAP` is enforced; within-race normalization makes `ModelProb` sum to 1 per race.
- [ ] Payout term uses gross odds `O`; the value judgement uses overround-removed `MarketProb` (gross-pay / de-overround-judge split).
- [ ] Stakes are rounded to 2dp.
- [ ] `KELLY_FRACTION`, `MIN_EDGE`, `CAP`, `BANKROLL` are knobs with the PRD defaults; `BANKROLL` is a documented provisional value with a comment noting it is finalized in `issues/005`.
- [ ] Unit tests under `tests/betting/` cover normalization, the Kelly fraction, the value gate, the cap, missing/`≤1`-price → 0, and multi-race frames. `python -m pytest tests/betting/` passes.
- [ ] `pre-commit run --all-files` (ruff + pyright strict) passes.

## Blocked by

None - can start immediately.

## User stories addressed

Reference by number from the parent PRD:

- User story 2 (larger stake on larger edge)
- User story 3 (smaller stake on marginal edge)
- User story 4 (zero stake when model does not beat the market)
- User story 6 (cap on the largest single stake)
- User story 8 (aggressiveness is a tunable knob)
- User story 9 (conservative *fraction* of full Kelly)
- User story 10 (judge against overround-removed market probability)
- User story 11 (payout uses the actual gross price)
- User story 12 (staking math isolated in a pure, dependency-free module)
- User story 22 (stakes rounded to pence)
- User story 23 (missing/unusable price → zero stake)
