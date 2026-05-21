## Parent PRD

`issues/prd.md`

## What to build

Create `Data/evaluate.py` — the 14-fold walk-forward evaluation script described in the *Evaluation script (evaluate.py)* and *Walk-forward fold structure* sections of the parent PRD. The script writes nothing to disk; all output goes to the console.

For each of the 14 days ending yesterday (inclusive):
1. Load the 7 months of raw `Results_*.csv` files ending the day before the target date.
2. Run the full feature engineering chain in-memory using the existing utilities in `data_transforms.py` and `data_analysis.py` (categorical encoding, speed calculation, horse stats, jockey stats).
3. Apply the `KnownHorseAndJockey == True` filter before passing data to any algorithm.
4. Call `fit` then `predict` on every algorithm in the registry.
5. Score predictions with the shared scoring utilities and print per-fold results.

After all 14 folds, print a consolidated summary table (one row per algorithm, showing overall accuracy and ROI).

## Acceptance criteria

- [ ] Running `python Data/evaluate.py` from the repo root completes without error against the existing `Data/Results_*.csv` files
- [ ] Per-fold console output shows: fold date, each algorithm name, accuracy, and ROI
- [ ] Final summary table shows each algorithm's overall accuracy and ROI across all 14 folds
- [ ] No files are written to disk during or after the run
- [ ] Horse and jockey statistics for each fold are derived from the same 7-month training window — not from pre-computed global stats files
- [ ] `KnownHorseAndJockey == True` filter is applied before any algorithm receives race data; a test in `Data/tests/test_evaluate.py` (or equivalent) verifies the filter removes the correct rows
- [ ] Races exceeding an algorithm's `max_horses` are excluded by that algorithm internally; the pipeline does not apply a global field-size cutoff
- [ ] Feature engineering uses `data_transforms.py` / `data_analysis.py` with no new intermediate CSV files produced

## Blocked by

- Blocked by `issues/001-algorithm-package-ridge-registry.md`
- Blocked by `issues/002-scoring-utilities.md`

## User stories addressed

- User story 1 (single command to compare all registered algorithms over 14 days)
- User story 2 (7-month training window per fold — no data leakage)
- User story 3 (14 individual race days, retraining per day)
- User story 4 (per-day accuracy and ROI printed as each fold completes)
- User story 5 (consolidated summary table at the end)
- User story 8 (no files written to disk)
- User story 9 (all feature engineering computed in-memory)
- User story 10 (horse and jockey stats computed from the same training window)
- User story 11 (all algorithms share the same feature engineering pipeline)
- User story 12 (races with unknown horses or jockeys excluded)
- User story 13 (each algorithm declares its own max field size)
