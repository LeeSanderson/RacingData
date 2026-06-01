## Parent PRD

`issues/prd.md`

## What to build

The HITL adoption decision, based on 009's comparison report. If the new config clears the
acceptance bar — frontier dominates the baseline at >= 50% coverage, gain stable across the
early-vs-late split, numbers consistent with the production anchor — promote it to
`ACTIVE_ALGORITHM`, confirm the abstain layer rides through `predict.py` in production (production
abstains the same way evaluation does), and update `evaluations.md` and memory with the honest
frontier + coverage numbers. If it does not clear the bar, record the rationale and leave the
baseline active. See the PRD "Acceptance bar" and "Workstream 4".

## Acceptance criteria

- [ ] An adoption decision is recorded explicitly against the acceptance bar.
- [ ] If adopted: `ACTIVE_ALGORITHM` points to the new abstain wrapper; `predict.py` abstains in production consistently with eval; `evaluations.md` and memory are updated with honest frontier + coverage numbers.
- [ ] If not adopted: the rationale is recorded and the current baseline remains active.
- [ ] A final confirmation that no shipped feature/filter input derives from odds.

## Blocked by

- Blocked by `issues/009-final-reeval-comparison-report.md`

## User stories addressed

- User story 3
- User story 28
- User story 29
- User story 30
- User story 31
