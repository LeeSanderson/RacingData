# Issue 001: Add a leakage warning to `evaluations.md`

## Parent PRD

`issues/prd.md`

## What to build

A prominent warning banner at the top of `evaluations.md`, added immediately and
independently of the code fix. The existing figures (e.g. the TSR-gated
`RatingsXGBoostAlgorithm` "0.78 accuracy" headline) are inflated by post-race
RPR/TSR leakage and must not be trusted while the fix is in progress. See the
PRD's "Problem Statement" and the "Documentation" implementation decision.

The banner should state, concisely:

- The numbers below are inflated by post-race `RacingPostRating`/`TopSpeedRating`
  leakage (these are assigned *from the run itself*, see the within-race Spearman
  table in the PRD).
- The real production accuracy from the 2026 `PredictionScores_*.csv` logs is
  ~0.265 (514 completed bets), versus the ~0.78 the gated evaluation claimed —
  roughly 3× inflation.
- These numbers will be replaced once the clean 180-fold re-evaluation completes
  (tracked by `issues/007-rewrite-evaluations-and-review-active-algorithm.md`).

Doc-only change. No code, no schema, no pipeline impact.

## Acceptance criteria

- [ ] `evaluations.md` opens with a clearly delimited warning block (e.g. a
      `> **⚠ LEAKAGE WARNING**` blockquote) before the first results table
- [ ] The warning names the leaking features (`RacingPostRating`,
      `TopSpeedRating`) and the train/serve skew mechanism in one or two sentences
- [ ] The warning cites the ~0.265 production anchor and the ~3× inflation versus
      the gated evaluation
- [ ] The warning points the reader to the in-progress fix (this PRD / issue 007)
- [ ] No existing content below the banner is deleted or renumbered (the inflated
      tables stay in place, just flagged as untrustworthy)

## Blocked by

None - can start immediately.

## User stories addressed

Reference by number from the parent PRD:

- User story 18
