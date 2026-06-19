# `docs/staking.md` honesty-caveats doc

## Parent PRD

`issues/prd.md` — "Implementation Decisions" (Staking strategy, probabilities normalized but NOT calibrated), "Out of Scope", "Further Notes", and User story 21 (limitations travel with the feature the way the MarketProb caveats do).

## What to build

A new `docs/staking.md` documenting the staking strategy and its honesty caveats, mirroring the style of `docs/data-pitfalls.md` / `docs/odds-capture.md`. It should state:

- **The strategy** — fractional Kelly with a value gate; the gross-pay / de-overround-judge split; one bet per covered race on the top pick.
- **The knobs and defaults** — `KELLY_FRACTION`, `MIN_EDGE`, `CAP`, `BANKROLL` (and that `BANKROLL` is a fixed, stateless notional scale, not a tracked balance).
- **The caveats** (the point of the doc):
  - probabilities are normalized but **not calibrated** (isotonic/Platt deferred; fractional Kelly is the sole buffer against miscalibration);
  - the backtest is an **SP-placeholder / diagnostic-only** mechanics check, **not real-money validated**;
  - the forward staked-outcome log (`issues/003`) is what makes calibration and an honest track record measurable later.

Cross-link `docs/data-pitfalls.md` (the MarketProb / SP-placeholder pitfall) and the `evaluations.md` staking diagnostic section (`issues/005`) so the limitations stay discoverable.

## Acceptance criteria

- [x] `docs/staking.md` exists, documenting the strategy, the config knobs + defaults, and the three honesty caveats (uncalibrated probabilities, SP-placeholder backtest, not real-money validated).
- [x] It cross-references `docs/data-pitfalls.md` and the `evaluations.md` staking diagnostic section, in the same caveat style as the MarketProb docs.
- [x] It states the deferred-calibration decision and that the forward staked-outcome log is what makes calibration revisitable.

## Blocked by

- Blocked by `issues/001-pure-betting-staking-module.md`
- Blocked by `issues/002-stake-column-in-todays-predictions.md`
- Blocked by `issues/004-diagnostic-staking-backtest.md`

(So the doc describes the real, shipped behaviour and can reference real backtest numbers. Best written after `issues/005` so the cited diagnostic figures are final.)

## User stories addressed

Reference by number from the parent PRD:

- User story 21 (staking strategy documented with its honesty caveats)
