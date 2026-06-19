# Wire stake into `predict.py` → `Stake` column in `TodaysPredictions.csv`

## Parent PRD

`issues/prd.md` — "Modules built / modified" (`predict.py` bullet), "Schema changes / contracts", "Pipeline wiring".

## What to build

Wire the pure betting module (`issues/001`) into the predict step (`race_analytics/scripts/predict.py`). After the active algorithm produces the full field via `predict_field(serve_data)` — and **before** the existing filter to `PredictedRank == 1` — call the staking module on that full frame, where within-race normalization and the already-materialized `MarketProb` (and the resolved decimal odds from `resolve_decimal_odds`) are available. Merge the resulting `Stake` onto the published rank-1 winner rows, and add `Stake` to the predict output column set (`_OUTPUT_COLS`).

The file stays one row per covered race; no-value / abstain races are **retained with `Stake = 0`**, never dropped, so `TodaysPredictions.csv` remains a complete record of what was considered. Per the PRD there is **no change to `run.ps1`** — the stake is produced inside the existing predict step.

The typical *magnitude* of the stake (the ~£1 anchor) depends on `BANKROLL`, which is calibrated in `issues/005`; this slice only has to make the column appear and carry correctly computed values for the provisional `BANKROLL`.

## Acceptance criteria

- [ ] Running the predict step (`predict --data Data`) writes `TodaysPredictions.csv` with a new `Stake` column.
- [ ] `Stake` is computed from the full `predict_field` frame so within-race normalization is over the whole field, not just the winner row.
- [ ] Every covered race appears exactly once; no-value / abstain races are retained with `Stake = 0`, not dropped.
- [ ] The resolved decimal odds (`resolve_decimal_odds`, forecast-when-present-else-SP) are available to the staking call in the serving frame; if `build_serving_from_stats` does not currently carry the price column through, thread it through so the payout term has real odds (otherwise stakes are uniformly 0).
- [ ] No change to the `run.ps1` step sequence.
- [ ] A test under `tests/scripts/` (mirroring `test_predict.py`) asserts the `Stake` column is present and that a hand-constructed field produces the expected non-zero / zero stakes end-to-end through predict.
- [ ] `pre-commit run --all-files` passes.

## Blocked by

- Blocked by `issues/001-pure-betting-staking-module.md`

## User stories addressed

Reference by number from the parent PRD:

- User story 1 (a `Stake` column next to each pick)
- User story 7 (no-bet races retained with zero stake, not dropped)
- User story 13 (stake computed from the full field's probabilities so within-race normalization is possible)
- User story 14 (no change to `run.ps1`'s step sequence)
