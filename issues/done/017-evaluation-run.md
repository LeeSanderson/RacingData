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

## Progress (2026-06-06)

All blockers resolved (issues 013–016 done). 2-fold smoke test (2 months training) completed cleanly:
- All 6 algorithms ran without errors across both folds.
- AbstainWrapperSplitAlgorithm is notably slower (~17s fit vs ~6s for others) due to training 3 sub-models.
- Feature engineering dominates per-fold time; estimated ~5–7 min/fold, so 180 folds ≈ 18–30 hours.

**Full run command (resume with --fold-offset N if interrupted):**

```
python -m race_analytics.scripts.evaluate `
  --folds 180 --training-months 7 `
  --algorithms "AbstainWrapperAlgorithm,AbstainWrapperGapAlgorithm,AbstainWeightedPositionAlgorithm,AbstainWrapperLTRAlgorithm,AbstainWrapperSplitAlgorithm,AbstainRecencyWeightedAlgorithm" `
  --save-results
```

Results saved incrementally to `evaluation_results_YYYYMMDD.csv` — each fold is flushed to disk immediately, so `--fold-offset N` can resume from fold N if the run is interrupted.
