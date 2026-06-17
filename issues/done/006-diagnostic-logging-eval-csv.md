## Parent PRD

`issues/prd.md` — "Diagnostic logging" (Implementation Decisions).

## What to build

Surface the market signal in the evaluation output CSV so its influence on each algorithm
can be inspected post-hoc.

In `race_analytics/scripts/evaluate.py` (`_CSV_COLUMNS` / `_build_csv_rows`): add, per
predicted runner, the `MarketProb` value (carried from the served `RaceData`, which now
holds it via `issues/002`) and the **resolved odds** (forecast → SP, via the `issues/005`
measurement path). The existing per-runner row layout and the incremental per-fold flush
are otherwise unchanged.

## Acceptance criteria

- [ ] The evaluation results CSV gains a `MarketProb` column and a resolved-odds column,
      populated per predicted runner.
- [ ] A short walk-forward run with `--save-results` writes a CSV whose new columns are
      populated (dense `MarketProb`; resolved odds present), and the run still completes.
- [ ] A test on `_build_csv_rows` asserts the new columns are emitted with the expected
      values for a small synthetic field.

## Blocked by

- Blocked by `issues/002-materialize-market-prob-serving-path.md`
- Blocked by `issues/005-measurement-through-resolver.md`

## User stories addressed

- User story 13 (`MarketProb` and resolved odds logged in the evaluation output CSV)
