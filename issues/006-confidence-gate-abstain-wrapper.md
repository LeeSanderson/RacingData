## Parent PRD

`issues/prd.md`

## What to build

The confidence half of the abstain layer. Build a **pure confidence-gate module** that, from a
race's per-horse win-probabilities, computes both the top-pick win-probability and the
gap-to-second-pick and decides keep/abstain against a threshold expressed as a **training-window
coverage quantile** (both metrics implemented). Build an **abstain wrapper algorithm** over
`ProxyTSRXGBoostAlgorithm` that applies the gate (the hard-race-rules gate is left as a no-op for
now), registered in the algorithm registry. Add **ROI-vs-coverage frontier** reporting and an
**early-vs-late stability split** to `evaluate.py`. See the PRD "Filter A" and "Evaluation
enrichment".

## Acceptance criteria

- [ ] A pure confidence module decides keep/abstain per race from per-horse probabilities, for both metrics, with thresholds derived from training-window coverage quantiles.
- [ ] An abstain wrapper algorithm is registered and, in eval, predicts on fewer than 100% of races as the threshold tightens.
- [ ] `evaluate.py` reports a ROI-vs-coverage frontier (sweeping the confidence threshold) and an early-vs-late split, with coverage shown alongside accuracy/ROI.
- [ ] The confidence module has pytest coverage: synthetic probabilities, both metrics, threshold/coverage edge cases, and the empty-race case.

## Blocked by

- Blocked by `issues/001-enriched-evaluation-output.md`

## User stories addressed

- User story 1
- User story 4
- User story 7
- User story 8
- User story 9
- User story 10
- User story 32
