# Evaluator reports `Kelly £` / `Kelly%` in the cross-fold Summary table

## Parent PRD

`issues/prd.md` — "Kelly-staked ROI in the evaluation metrics"

## What to build

The headline feature: make `race_analytics/scripts/evaluate.py` report Kelly net £ and
Kelly coverage % per algorithm in the cross-fold **Summary** table, computed inline from
the same data the diagnostic backtest reads — so a single evaluator run gives the staked
return without running `backtest_staking.py` as a second pass.

The evaluator already builds, for every (algorithm, fold), the full-field result frame it
writes to the CSV via `_build_csv_rows` (carrying `WinProbability`, `MarketProb`,
`ResolvedOdds`, `FinishingPosition`, `RaceId`, `Algorithm`). Retain those per-fold frames
and feed their concatenation through the shared `betting` backtest summariser introduced
in issue 001 — guaranteeing the inline figure equals the diagnostic script's figure by
construction. Cross-fold aggregation is **additive**: concatenate the retained frames and
summarise once, never average per-fold ratios (PRD "Cross-fold aggregation is additive").

Append two columns — `Kelly £` and `Kelly%` — to the Summary table, after the existing
columns, with **no** extra diagnostic label (the Summary stays compact; the caveat lives
in the diagnostic script and docs). The metric is locked: Kelly headline = net £ P&L on
decimal odds (won → `stake × (odds − 1)`, lost → `− stake`), summed over placed bets;
coverage % = placed bets ÷ settleable races — the same accounting as flat ROI, differing
only by variable stake size and the value gate.

Algorithms that emit no win probability (the regression models) produce no staked bets and
must report `n/a` / 0% coverage rather than a misleading zero or an error. The Kelly
figures are computed on **every** run and must not depend on `--save-results`.

This slice **includes the parity test** (PRD Testing Decisions, "New parity test" / user
story 15): a test asserting the evaluator's inline Kelly aggregation over a set of per-fold
frames produces the same summary as calling the shared `betting` backtest function over the
concatenation of those frames.

Do **not** change the existing accuracy / flat-£1 ROI / favourite-baseline / timing
columns, the algorithm-selection / promotion policy, or the ROI-vs-coverage frontier
output.

## Acceptance criteria

- [ ] The evaluator retains the per-(algorithm, fold) full-field frames and computes Kelly net £ + coverage % by summarising their concatenation with the shared `betting` function (additive aggregation, single summarise call)
- [ ] The Summary table gains `Kelly £` and `Kelly%` columns appended after the existing columns, with no diagnostic label
- [ ] A non-probabilistic algorithm (e.g. a regression model) shows `n/a` / `0%` for Kelly, not `0.0` or an error
- [ ] Kelly columns appear when running without `--save-results` (e.g. `python -m race_analytics.scripts.evaluate --folds 2 --training-months 2`)
- [ ] Existing accuracy / ROI / favourite / timing columns and the ROI-vs-coverage frontier are byte-for-byte unchanged
- [ ] A pytest case asserts the inline aggregation equals the shared backtest summary over the same concatenated frames (the parity guarantee)
- [ ] pytest covers the additive cross-fold aggregation (sum returns and counts, recompute coverage at the end) on an eval-results-shaped fixture
- [ ] `pytest tests/` passes

## Blocked by

- Blocked by `issues/001-move-staking-summary-into-betting.md`

## User stories addressed

Reference by number from the parent PRD:

- User story 1 (Kelly net £ in the cross-fold Summary table)
- User story 2 (Kelly coverage % alongside Kelly net £)
- User story 3 (existing metrics unchanged)
- User story 6 (inline figure equals `backtest_staking.py`)
- User story 7 (same odds / net-P&L convention as flat ROI)
- User story 8 (additive cross-fold aggregation)
- User story 9 (non-probabilistic algorithms show `n/a` / 0%)
- User story 10 (Kelly columns appear without `--save-results`)
- User story 13 (no extra diagnostic label on the evaluator's Kelly columns)
- User story 15 (parity test enforcing inline == offline backtest)
