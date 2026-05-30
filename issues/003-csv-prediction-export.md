## Parent PRD

`issues/prd.md`

## What to build

Add optional CSV export to `evaluate.py` that writes one row per algorithm per race prediction, including race metadata, correctness, and raw model score. Controlled by two new CLI flags.

End-to-end behaviour: running `evaluate.py --save-results` produces `evaluation_results_YYYYMMDD.csv` in the current directory. Running with `--results-file my_run.csv` (with or without `--save-results`) writes to that path instead. No file is written if neither flag is passed.

See the CSV output sections of the parent PRD.

## Acceptance criteria

- [ ] `--save-results` flag (boolean store-true) enables CSV output
- [ ] `--results-file PATH` flag sets the output path; passing it without `--save-results` implicitly enables saving
- [ ] Default filename when no path is given: `evaluation_results_YYYYMMDD.csv` using today's (run) date, written to the current working directory
- [ ] No CSV file is written when neither flag is passed
- [ ] CSV contains exactly these columns: `FoldDate`, `Algorithm`, `RaceId`, `HorseId`, `CourseName`, `Surface`, `Going`, `RaceType`, `DistanceInMeters`, `FinishingPosition`, `DecimalOdds`, `PredictedScore`
- [ ] `Surface`, `Going`, `RaceType` contain raw string values (e.g. `Turf`, `Good`, `Flat`), not one-hot integers
- [ ] `PredictedScore` is populated from `PredictedSpeed` when the algorithm's prediction DataFrame contains that column; otherwise the column is present but null/empty
- [ ] Each row represents the algorithm's top-1 prediction for one race (one row per algorithm per race per fold)
- [ ] Rows are assembled incrementally inside the fold loop and written once at the end of all folds
- [ ] Unit tests in `tests/scripts/test_evaluate.py` assert:
  - `--save-results` produces a file with the correct column schema
  - `--results-file PATH` without `--save-results` also produces output at `PATH`
  - `PredictedScore` is populated when `PredictedSpeed` is present and null when absent
  - `Surface`, `Going`, `RaceType` values in the CSV are raw strings
  - No file is written when neither flag is passed

## Blocked by

None — can start immediately.

## User stories addressed

- User story 6
- User story 7
- User story 8
- User story 9
- User story 10
- User story 11
- User story 12
- User story 13
- User story 14
- User story 15
- User story 16
- User story 17
- User story 18 (partially — CSV assembly extracted into a testable helper)
