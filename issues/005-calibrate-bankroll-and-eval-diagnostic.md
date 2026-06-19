# Calibrate `BANKROLL` + write the SP-placeholder diagnostic in `evaluations.md`

## Parent PRD

`issues/prd.md` — "Configuration knobs" (`BANKROLL` derived from the backtest stake distribution, median ≈ £1), "Modules built / modified" (diagnostic flagged in the findings doc), "Further Notes", "Out of Scope" (no promotion off the diagnostic backtest).

## What to build

Run the `issues/004` backtest over the latest walk-forward results, derive `BANKROLL` as the scale constant that lands the **median advised stake ≈ £1** given the observed stake distribution, and set that as the shipped `BANKROLL` default in the betting module (replacing the provisional value from `issues/001`). Then record the result as a new dated diagnostic section in `evaluations.md`, flagged ⚠️ SP-PLACEHOLDER / DIAGNOSTIC-ONLY / NOT a promotion decision — mirroring the existing "13-fold MarketProb diagnostic" section: Kelly ROI vs flat-£1 ROI, coverage, the stake distribution, and the chosen `BANKROLL`.

This must **not** touch `ACTIVE_ALGORITHM` (`race_analytics/algorithms/__init__.py`) — that section documents the prediction algorithm, not the staking strategy.

## Acceptance criteria

- [ ] `BANKROLL` in `race_analytics/betting/` is set to the value that lands the median advised stake ≈ £1 over the backtest's stake distribution, with a comment explaining the derivation (not a PRD/ticket reference).
- [ ] `evaluations.md` gains a new dated diagnostic section, flagged SP-placeholder / diagnostic-only / no-promotion, reporting Kelly ROI vs flat-£1 ROI, coverage, the stake distribution, and the chosen `BANKROLL`.
- [ ] That section explicitly states why the backtest can't validate profitability (≈0% real forecast coverage in history → it measures the SP placeholder), per the PRD's "Further Notes".
- [ ] `ACTIVE_ALGORITHM` is unchanged.
- [ ] Re-running the predict step after the `BANKROLL` change produces stakes whose typical magnitude is ≈ £1.
- [ ] `pre-commit run --all-files` passes.

## Blocked by

- Blocked by `issues/004-diagnostic-staking-backtest.md`

## User stories addressed

Reference by number from the parent PRD:

- User story 5 (typical stake sits around a familiar £1 unit)
- User story 16 (backtest clearly flagged SP-placeholder / diagnostic-only)
- User story 17 (stake distribution used to tune the fixed scale constant)
