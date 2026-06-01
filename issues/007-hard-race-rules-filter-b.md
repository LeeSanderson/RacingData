## Parent PRD

`issues/prd.md`

## What to build

The hard-race-rules half of the abstain layer (Filter B). Build a **pure rules module**
implementing the 2-4 rules approved in 003, derived from race attributes (field size, class, race
type, handicap flag inferred from `RatingBand` presence). Plug it into the abstain wrapper as the
second gate, so a race is bet only if it passes **both** the confidence gate and the rules. Tests
for each rule and the combined gate. See the PRD "Filter B".

## Acceptance criteria

- [ ] A pure rules module flags the approved hard-race shapes; structural blanks (no class / no rating band) are handled.
- [ ] The wrapper applies both gates; rule-flagged races are excluded from predictions.
- [ ] At the chosen operating point with both gates active, combined coverage stays >= 50% of predictable races.
- [ ] pytest covers each individual rule and the combined gate.

## Blocked by

- Blocked by `issues/003-review-approve-rules-and-features.md`
- Blocked by `issues/006-confidence-gate-abstain-wrapper.md`

## User stories addressed

- User story 2
- User story 3
- User story 12
- User story 32
