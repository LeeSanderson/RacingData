# Stake-weighted return figure in the `validate` log output

## Parent PRD

`issues/prd.md` — "Modules built / modified" (forward-logging bullet: "Optionally make the handler's logged return figure stake-weighted").

## What to build

Optional polish on the `validate` command handler (`ValidateRaceCardPredictionsCommandHandler`). Today it logs a flat-£1 ROI figure (stake of 1 per race). Replace or augment that with a **stake-weighted** figure using the `Stake` now carried on each prediction-score record (`issues/003`):

```
(Σ stake·odds of winners + Σ returned stake [void / non-runner] − Σ stake of losers) / Σ stake
```

This makes the daily run report staked performance, not just flat-£1 performance. It must degrade gracefully when `Stake` is absent or all-zero (e.g. fall back to the existing flat-£1 figure rather than divide by zero).

## Acceptance criteria

- [ ] The `validate` handler logs a stake-weighted return computed from the per-pick `Stake` and the settled odds/outcome, alongside or instead of the flat-£1 figure.
- [ ] Predictions with no `Stake` column / all-zero stakes do not divide-by-zero or crash (graceful fallback).
- [ ] A handler test asserts the stake-weighted figure for a small fixture (at least one winner and one loser with known stakes and odds).
- [ ] `dotnet test` passes.

## Blocked by

- Blocked by `issues/003-carry-stake-through-validate-handler.md`

## User stories addressed

Reference by number from the parent PRD:

- User story 19 (option of a stake-weighted return figure in the validate step's log output)
