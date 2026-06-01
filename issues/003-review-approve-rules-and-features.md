## Parent PRD

`issues/prd.md`

## What to build

Human review of the diagnostic output from 002. Approve a short list of **2-4 hard-race rules**
to implement (each justified as both intuitive and stable across the window), and make the
**go/no-go decision on the Tier-2 builder-extension features** (008). Record the approved rules in
a form the Filter B slice (007) can consume directly. This is the HITL half of the diagnostic.
See the PRD "Filter B" and the Workstream 2 tiering notes.

## Acceptance criteria

- [ ] 2-4 hard-race rules are selected from the diagnostic's candidate list, each with a recorded justification (intuitive + stable).
- [ ] A recorded go/no-go decision on whether Tier-2 features (008) are worth building.
- [ ] The approved rules are written down (in this issue or a linked note) precisely enough for 007 to implement without re-deriving them.

## Blocked by

- Blocked by `issues/002-diagnostic-analysis-script.md`

## User stories addressed

- User story 12
