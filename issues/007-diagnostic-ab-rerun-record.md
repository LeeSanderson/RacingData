## Parent PRD

`issues/prd.md` — "Adoption is gated on honest data, not this run" (Implementation
Decisions), plus "Further Notes" (known risks; read the accuracy jump correctly).

## What to build

Run the full A/B walk-forward comparison across **every registered algorithm** with
`MarketProb` now available, and record the results as a **diagnostic** — explicitly NOT a
promotion decision. Because forecast coverage in history is ~zero, this eval is measuring
the SP placeholder, not the forecast feature production will serve on.

- Re-run the walk-forward eval over all algorithms in `ALGORITHMS` (fold count is the
  implementer's call at run time — the PRD says "full walk-forward comparison" and the
  cost is ~6–8 min/fold × 16 algorithms; choose a depth that gives a clear per-algorithm
  read without committing to a fixed number here).
- Record the per-algorithm accuracy / ROI / coverage in `evaluations.md` under a clearly
  flagged **"SP-placeholder / diagnostic"** section, so nobody later mistakes these for
  decision-grade forecast results.
- Document the known eval/production divergence: the expected accuracy jump reflects the
  classifiers leaning on the (SP-defined) favourite — "following the favourite", not a
  genuine forecast-time edge.
- **Do not change `ACTIVE_ALGORITHM`.**

## Acceptance criteria

- [ ] The eval has been run across all registered algorithms with `MarketProb` available
      (per-fold results saved via `--save-results`).
- [ ] `evaluations.md` has a new, clearly-labelled SP-placeholder/diagnostic section with
      each algorithm's accuracy/ROI/coverage and the "following-the-favourite" caveat.
- [ ] `race_analytics/algorithms/__init__.py` `ACTIVE_ALGORITHM` is unchanged (verified by
      diff: no edit to the active-algorithm selection).

## Blocked by

- Blocked by `issues/004-expose-market-prob-optional-predictors.md`
- Blocked by `issues/005-measurement-through-resolver.md`
- Blocked by `issues/006-diagnostic-logging-eval-csv.md`

## User stories addressed

- User story 14 (full A/B re-run across every registered algorithm)
- User story 15 (results recorded under a flagged SP-placeholder/diagnostic section)
- User story 16 (production `ACTIVE_ALGORITHM` left untouched)
- User story 19 (known SP-vs-forecast divergence documented)
