## Parent PRD

`issues/prd.md`

## What to build

Add the Tier-1 features that need **no new card columns**: wire the existing-but-unused
`WeightChange` and `DistanceChange` into the predictor set, add an explicit `FieldSize` (and, if
useful, a `RelFieldSize` normalised against a historical/card-derived baseline), and
surface-switch / code-switch (flat <-> jumps) flags derived from the card vs the previous-race
`LastRace*` one-hots. Extend the transforms tests. See the PRD "New feature transforms".

Priority among these is informed by 002's nominations, but the inputs are all already present in
the merged prediction frame, so this can start immediately.

## Acceptance criteria

- [ ] `WeightChange` and `DistanceChange` appear in the model's feature set and are populated for horses with prior-race history.
- [ ] `FieldSize` is an explicit feature; any `RelFieldSize` is normalised against a historical/card-derived baseline, never a same-day cross-race or odds quantity.
- [ ] Surface-switch and code-switch flags are computed from card vs previous-race attributes.
- [ ] `tests/features/test_transforms.py` covers the new columns, including missing prior-race history (NaN tolerance).
- [ ] A short eval run completes with the new features in use.

## Blocked by

None - can start immediately (feature priority informed by `issues/003-review-approve-rules-and-features.md`).

## User stories addressed

- User story 14
- User story 15
- User story 20
