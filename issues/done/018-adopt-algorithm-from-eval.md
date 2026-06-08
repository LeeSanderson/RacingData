## Parent PRD

`issues/prd.md`

## What to build

Review the saved eval results from `issues/017-evaluation-run.md` and adopt any variant that beats the current −£62 ROI baseline with a stable early-vs-late gain. ROI and accuracy can diverge significantly — see PRD §Further Notes — so ROI is the primary gate.

**Adoption criteria** (from PRD §Evaluation run):

- Primary gate: ROI > −62 (improvement over current baseline).
- Secondary: stable early-vs-late ROI gain (improvement not confined to one time period).
- If multiple variants pass, adopt the one with the highest ROI.
- Update `ACTIVE_ALGORITHM` in `race_analytics/algorithms/__init__.py` and record results in `evaluations.md`.
- If no variant passes, record a no-change decision with reasoning in `evaluations.md`.

## Acceptance criteria

- [ ] Eval results reviewed for all six algorithms.
- [ ] Adoption decision documented in `evaluations.md`: either the winning variant is named with its ROI/accuracy/coverage figures and early-vs-late split, or a no-change decision is recorded with reasoning.
- [ ] If a new algorithm is adopted, `ACTIVE_ALGORITHM` in `__init__.py` points to the winning wrapped variant.

## Blocked by

- Blocked by `issues/017-evaluation-run.md`

## User stories addressed

- User story 15
