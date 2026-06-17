## Parent PRD

`issues/prd.md` — "Materialize in two non-shared places" (place **a**) and
"Test the train/serve parity explicitly" (Testing Decisions).

## What to build

Make the evaluation harness's in-memory feature-engineering step produce `MarketProb` on
the **training** path, so that what a model trains on matches what it predicts on. The
harness does not re-run the canonical serving transform chain, so `MarketProb` must be
produced independently here (both places call the `issues/001` helper).

In `race_analytics/scripts/evaluate.py`:

- Start carrying `ForecastDecimalOdds` alongside the existing `DecimalOdds` in the
  harness keep-columns (`_KEEP_COLS`) so the forecast survives into the training frame
  (graceful when the column is absent, as it is across all historic results today).
- Compute `MarketProb` in `_engineer_features` via the `issues/001` helper.

Then add the **train/serve parity test**: a runner's `MarketProb` is computed the same
way whether it arrives via the harness training path (`_engineer_features`) or via the
canonical serving transform (`calculate_market_prob`), so the documented two-place
materialization cannot silently drift.

## Acceptance criteria

- [ ] `_KEEP_COLS` includes `ForecastDecimalOdds`; `_engineer_features` output carries a
      dense `MarketProb` column.
- [ ] A test asserts `calculate_market_prob` / the helper produces the column on a
      **Results-shaped** frame (with the forecast column present) — per PRD Testing
      Decisions.
- [ ] A parity test asserts a runner's `MarketProb` is identical via the training path
      and the canonical serving transform on equivalent input.
- [ ] A short walk-forward invocation (small folds) runs without error and the predicted
      population is unchanged vs. before this slice.

## Blocked by

- Blocked by `issues/001-market-prob-resolver-helper.md`
- Blocked by `issues/002-materialize-market-prob-serving-path.md`

## User stories addressed

- User story 7 (feature materialized identically on training and serving paths)
