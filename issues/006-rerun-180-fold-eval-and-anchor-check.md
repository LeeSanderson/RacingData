# Issue 006: Re-run the 180-fold walk-forward eval + production-anchor check

## Parent PRD

`issues/prd.md`

**Type: HITL** — a long characterisation run with no pass/fail bar; a human
interprets the results and confirms the leak is gone.

## What to build

With the corrected algorithms (issues 003, 004) and trimmed card builders (issue
005) in place, run an honest leak-free evaluation and check it against the real
production anchor. See the PRD's "Re-evaluation and re-baselining" decision.

- Run `python -m race_analytics.scripts.evaluate --folds 180 --training-months 7`
  over the corrected algorithms against the market-favourite, ridge-regression and
  xgboost baselines. Capture accuracy, ROI, coverage (races predicted) and any
  field-size breakdowns.
- Compute the real production accuracy/ROI from the 2026 `PredictionScores_*.csv`
  logs (~0.265 accuracy, 514 completed bets) as the reality anchor.
- Sanity-check that the cleaned gated-strategy evaluation accuracy lands in the
  same ballpark as the ~0.265 anchor (a rough match, not a head-to-head replay —
  the matched backtest is explicitly out of scope).

This is a verification activity, not an automated test. The captured numbers feed
issue 007 (rewrite `evaluations.md` and review `ACTIVE_ALGORITHM`).

## Acceptance criteria

- [ ] 180-fold walk-forward evaluation completes for the corrected
      `RatingsXGBoost` (gated + ungated) and `ProxyTSRXGBoost` (+ tuned)
      algorithms alongside the three baselines, with the per-algorithm
      accuracy/ROI/coverage summary captured
- [ ] Real production accuracy/ROI computed from the `PredictionScores_*.csv` logs
      and recorded (expected ~0.265 accuracy)
- [ ] A short written comparison confirms the cleaned gated-strategy accuracy is
      near the ~0.265 anchor (i.e. the TSR-gated 0.60–0.78 headline has collapsed),
      providing evidence the leak is gone
- [ ] Results are captured in a form ready to drop into `evaluations.md` (issue
      007)

## Blocked by

- Blocked by `issues/003-ratings-xgboost-previous-race-ratings.md`
- Blocked by `issues/004-proxy-tsr-xgboost-as-of-date-proxy.md`
- Blocked by `issues/005-trim-rating-columns-from-card-builders.md`

## User stories addressed

Reference by number from the parent PRD:

- User story 16
- User story 17
- User story 22 (confirms the `run.ps1` build → predict flow still works on the
  corrected pipeline)
