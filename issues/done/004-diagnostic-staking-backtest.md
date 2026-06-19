# Diagnostic staking backtest script

## Parent PRD

`issues/prd.md` — "Modules built / modified" (diagnostic backtest bullet), "Testing Decisions", "Further Notes" (why the backtest can't validate profitability yet).

## What to build

A new analysis script `race_analytics/scripts/backtest_staking.py` (convention parallel to `forecast_vs_sp.py`) that replays the **same** pure betting module (`issues/001`) over the saved walk-forward evaluation-results CSVs (`evaluation_results_*.csv`), which already carry `WinProbability`, `MarketProb`, `ResolvedOdds`, `FinishingPosition`, and `FieldSize`. For each fold's rank-1 picks it computes the advised stake, then reports:

- Kelly-staked ROI vs flat-£1 ROI,
- coverage (fraction of races actually bet), and
- the stake distribution (median / mean / percentiles) — the input the `BANKROLL` calibration in `issues/005` needs.

It must reuse the production staking functions (so the backtest also exercises them) rather than re-implementing the math. Its console output must be flagged SP-placeholder / diagnostic-only / no-promotion, consistent with the MarketProb eval discipline; the written-up findings section in `evaluations.md` is `issues/005`.

## Acceptance criteria

- [ ] `python -m race_analytics.scripts.backtest_staking` (taking a results-file argument, matching the `forecast_vs_sp` CLI convention) runs over an `evaluation_results_*.csv` and prints Kelly ROI, flat-£1 ROI, coverage, and a stake-distribution summary.
- [ ] It imports and calls the `issues/001` staking functions directly — no re-implementation of the Kelly fraction, gate, or cap.
- [ ] The console output carries an explicit SP-placeholder / diagnostic-only / no-promotion caveat.
- [ ] A thin behavioural test under `tests/scripts/` runs it over a small fixture results frame and asserts the expected summary fields exist and are internally consistent (e.g. coverage in `[0, 1]`; flat-£1 ROI matches a hand-computed value).
- [ ] `pre-commit run --all-files` passes.

## Blocked by

- Blocked by `issues/001-pure-betting-staking-module.md`

## User stories addressed

Reference by number from the parent PRD:

- User story 15 (diagnostic backtest replaying the staking plan over historical eval results)
- User story 17 (backtest reports the distribution of stakes it produces)
