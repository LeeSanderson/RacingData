## Parent PRD

`issues/prd.md`

## What to build

Run a single 180-fold walk-forward evaluation covering all four new wrapped variants alongside the existing `AbstainWrapperAlgorithm` and `AbstainWrapperGapAlgorithm` baselines, saving results to disk for review in `issues/018-adopt-algorithm-from-eval.md`.

**Run command** (from PRD §Evaluation run):

```
python -m race_analytics.scripts.evaluate \
  --folds 180 --training-months 7 \
  --algorithms "AbstainWrapperAlgorithm,AbstainWrapperGapAlgorithm,AbstainWeightedPositionAlgorithm,AbstainWrapperLTRAlgorithm,AbstainWrapperSplitAlgorithm,AbstainRecencyWeightedAlgorithm" \
  --save-results
```

Use `--fold-offset` for crash recovery across sessions (~75 hours total). Consider running HeadGear-only first (2 algorithms, ~10 hours) to confirm headgear adds value before committing to the full run.

## Acceptance criteria

- [ ] 180-fold eval completes for all six algorithms with `--save-results`.
- [ ] Saved results include ROI (primary), accuracy, coverage, and early-vs-late stability split for each variant.
- [ ] No algorithm errors or silent fold failures in the run log.

## Blocked by

- Blocked by `issues/013-weighted-position-proxy-tsr-algorithm.md`
- Blocked by `issues/014-ltr-proxy-tsr-algorithm.md`
- Blocked by `issues/015-split-race-type-algorithm.md`
- Blocked by `issues/016-recency-weighted-proxy-tsr-algorithm.md`

## User stories addressed

- User story 13
- User story 14
