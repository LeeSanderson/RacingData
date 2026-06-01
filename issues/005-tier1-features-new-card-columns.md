## Parent PRD

`issues/prd.md`

## What to build

Add the Tier-1 features that **require new card columns**. Carry `Class`, `Age`, `StallNumber`,
`Pattern`, `RatingBand`, `AgeBand`, `SexRestriction` through the prediction card (`predict.py`)
and the eval card extraction (no rating or odds columns). Add a `RaceClass` ordinal encoding,
`Age`/`RelAge` (reusing the race-context "Rel" machinery), draw features (`DrawPct`/`RelDraw`,
flat-only), and race quality/eligibility one-hots. Add structurally-sparse features to the
NaN-tolerant predictor list. Extend transforms tests including blank/null handling. See the PRD
"New feature transforms" and "Schema and wiring changes".

## Acceptance criteria

- [ ] `predict.py` and the eval card extraction carry the added card columns; `predict.py` still produces `TodaysPredictions.csv` without error.
- [ ] `RaceClass` ordinal encoding handles "Other"/blank via a dedicated bucket.
- [ ] Draw features are computed for flat races and tolerate null draw on jumps.
- [ ] `Age`/`RelAge` and the quality/eligibility one-hots (including a "None"/blank category) are in the feature set.
- [ ] `tests/features/test_transforms.py` covers the ordinal encoding, draw null-on-jumps, and one-hot blank categories.

## Blocked by

None - can start immediately (feature priority informed by `issues/003-review-approve-rules-and-features.md`).

## User stories addressed

- User story 16
- User story 17
- User story 18
- User story 19
- User story 33
