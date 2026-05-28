# Issue 006 — Full 180-fold re-evaluation on the broader race sample

## Parent PRD

`issues/prd.md` — Phase B.

## What to build

Run the full leak-free 180-fold walk-forward evaluation against the post-fix
configuration to measure the real coverage and accuracy of the XGBoost-family
algorithms on the broader race sample. This is the expensive validation step
(~5h wall time) the PRD intentionally pays once at the end.

- Use the existing `race_analytics/scripts/evaluate.py` pipeline (180 folds,
  same walk-forward setup as the Phase A baseline).
- Algorithms in scope: every entry in `ALGORITHMS` —
  `RidgeRegressionAlgorithm`, `XGBoostAlgorithm`, `RatingsXGBoostAlgorithm`,
  `RatingsXGBoostUngatedAlgorithm`, `ProxyTSRXGBoostAlgorithm`,
  `TunedProxyTSRXGBoostAlgorithm`. `MarketFavouriteBaseline` runs alongside
  as the non-ML anchor.
- Capture, per algorithm:
  - Race count (the n that contributes to per-pick accuracy).
  - Per-pick accuracy.
  - Any other headline metric the existing evaluation script reports.
- Sanity expectations (deviations should be investigated before issue 007
  starts):
  - XGBoost-family race coverage jumps from ~415 to ~1,650 races.
  - Ridge race coverage is roughly unchanged from Phase A.
  - Per-algorithm accuracy on the broader sample is in the same ballpark as
    the Phase-A baseline — no large unexplained regressions.

### HITL because

This issue requires a human to (a) kick off the ~5h evaluation, (b) keep an
eye on it, and (c) sanity-check the resulting numbers against the
expectations above before they become the input to issue 007.

## Acceptance criteria

- [ ] Full 180-fold evaluation completes against the post-issue-005 code.
- [ ] Per-algorithm race count and accuracy captured (committed as a run log
      or pasted into the PR / issue 007 brief — match whatever convention
      `evaluations.md` already uses).
- [ ] XGBoost-family race coverage materially increased vs the 415-race
      Phase-A baseline.
- [ ] Ridge race coverage unchanged within rounding vs Phase-A baseline.
- [ ] No regression in per-algorithm accuracy that the team cannot explain
      from the larger sample (the broader sample may pull accuracy down
      slightly — that's expected; an unexplained collapse is not).

## Blocked by

- Blocked by `issues/005-last3-coverage-fix-and-xgboost-opt-in.md`.

## User stories addressed

- User story 1
- User story 13
- User story 17
