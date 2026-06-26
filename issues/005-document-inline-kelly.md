# Update `docs/staking.md` and `evaluations.md` to record inline Kelly reporting

## Parent PRD

`issues/prd.md` — "Kelly-staked ROI in the evaluation metrics"

## What to build

Documentation-only slice. Update `docs/staking.md` and the methodology note in
`evaluations.md` to state that Kelly net £ / coverage % is now reported **inline by the
evaluator** at all three sites (the per-fold line, the cross-fold Summary table, and the
Early-vs-Late stability split), so the documentation matches the tool.

Preserve the honesty framing: the inline Kelly numbers carry no diagnostic label inside the
evaluator (kept compact), while the SP-placeholder / diagnostic-only caveat continues to
live in `backtest_staking.py`'s banner and in the docs. The same SP-placeholder reasoning
documented for the existing MarketProb and staking diagnostics applies to these inline
numbers until the ≥80% forecast-coverage re-eval trigger fires. Reaffirm that algorithm
selection / promotion still rests on flat ROI + early/late stability while history is
SP-derived (PRD "No selection-policy change"; user story 17), with Kelly riding along as an
informational signal only.

No code changes.

## Acceptance criteria

- [ ] `docs/staking.md` states that Kelly £/coverage is reported inline by the evaluator (per-fold line, Summary table, Early-vs-Late split) and retains the SP-placeholder caveat
- [ ] The methodology note in `evaluations.md` records the inline Kelly reporting and reaffirms that selection stays flat-ROI + early/late stability while history is SP-derived
- [ ] No source or test files are modified by this slice

## Blocked by

- Blocked by `issues/002-evaluator-kelly-summary-table.md`
- Blocked by `issues/003-kelly-on-per-fold-line.md`
- Blocked by `issues/004-kelly-in-early-late-split.md`

## User stories addressed

Reference by number from the parent PRD:

- User story 16 (`docs/staking.md` and `evaluations.md` record inline Kelly reporting)
- User story 17 (selection still rests on flat ROI + stability; Kelly is informational) — reaffirmed in the docs
