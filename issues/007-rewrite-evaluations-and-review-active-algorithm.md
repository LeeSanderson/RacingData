# Issue 007: Rewrite `evaluations.md` and review `ACTIVE_ALGORITHM`

## Parent PRD

`issues/prd.md`

**Type: HITL** — choosing the production algorithm on leak-free evidence is a
judgement call, and the document rewrite reflects that decision.

## What to build

Using the clean 180-fold results and the production-anchor comparison from issue
006, replace the inflated content in `evaluations.md` and re-decide the active
algorithm. See the PRD's "Documentation" and "Re-evaluation and re-baselining"
decisions.

- Rewrite `evaluations.md` with the corrected numbers: honest accuracy, ROI,
  coverage and field-size breakdowns for the corrected algorithms versus the
  baselines. The leakage-warning banner from issue 001 is removed or replaced by
  the clean narrative (the inflated tables are no longer the headline). Expect the
  TSR-gated headline to have collapsed and accuracy to land ~0.25–0.30.
- Review `ACTIVE_ALGORITHM` in `race_analytics/algorithms/__init__.py` and update
  it if the leak-free evidence supports a different choice (e.g. away from the
  TSR-gated `RatingsXGBoostAlgorithm`).

## Acceptance criteria

- [ ] `evaluations.md` reflects the clean 180-fold numbers; the inflated
      post-race-leakage figures and the issue-001 warning banner are no longer
      presented as current
- [ ] The document records the production-anchor comparison (cleaned gated
      strategy vs ~0.265) as evidence the leak is gone
- [ ] `ACTIVE_ALGORITHM` is reviewed; if changed, `algorithms/__init__.py` is
      updated and the choice is justified against the leak-free results (and a
      `predict` run still produces `TodaysPredictions.csv`)
- [ ] The "which algorithm is active and why" rationale is captured in
      `evaluations.md`

## Blocked by

- Blocked by `issues/006-rerun-180-fold-eval-and-anchor-check.md`

## User stories addressed

Reference by number from the parent PRD:

- User story 19
- User story 20
