## Parent PRD

`issues/prd.md`

## What to build

Make per-horse model confidence observable in evaluation. Modify the binary-win-classifier
algorithm so callers can obtain the **full predictable field with each horse's `WinProbability`**
(the existing rank-1, one-pick-per-race selection used in production must be preserved). Modify
`evaluate.py` so the saved results CSV carries those per-horse win-probabilities plus race-level
context columns (at minimum field size and race class). See the PRD "Per-horse probability
exposure" and "Evaluation enrichment" implementation decisions.

This is the foundation that the diagnostic (002) and the confidence gate (006) build on.

## Acceptance criteria

- [ ] The classifier can return per-horse win-probabilities for the full predictable field, not only the top pick, without changing the production one-pick-per-race result.
- [ ] `python -m race_analytics.scripts.evaluate --folds 2 --training-months 2 --save-results` writes a results CSV whose rows carry a populated `WinProbability` column.
- [ ] The results CSV includes race-level context columns (at least field size and race class) per row.
- [ ] The existing eval summary (accuracy / ROI / timing) still prints unchanged for the top-pick selection.

## Blocked by

None - can start immediately.

## User stories addressed

- User story 6
- User story 13
