## Parent PRD

`issues/prd.md`

## What to build

The AFK run-and-measure half of final evaluation. Fast-screen the implemented features on the
plain `XGBoostAlgorithm` (~1 min for 180 folds), select the winners, then run the full 180-fold
`ProxyTSRXGBoostAlgorithm` re-eval with the selected features + both abstain gates. Produce the
comparison report: the new config's **ROI-vs-coverage frontier vs the current ProxyTSR baseline**,
the **early-vs-late stability** split, and the **production-anchor** sanity check (0.265 / +£78).
Confirm no feature or filter input derives from odds. The adoption decision is the separate issue
010. See the PRD "Workstream 4" and "Acceptance bar".

## Acceptance criteria

- [ ] A fast-XGBoost feature screen ranks the new features and selects those that improve the screening metric.
- [ ] A full 180-fold ProxyTSR re-eval runs with the selected features + abstain layer and writes results.
- [ ] The report compares the new config's ROI-vs-coverage frontier to the baseline at >= 50% coverage, shows early-vs-late stability, and the anchor sanity-check.
- [ ] A check confirms no feature/filter input is derived from odds.

## Blocked by

- Blocked by `issues/004-tier1-features-no-new-card-columns.md`
- Blocked by `issues/005-tier1-features-new-card-columns.md`
- Blocked by `issues/006-confidence-gate-abstain-wrapper.md`
- Blocked by `issues/007-hard-race-rules-filter-b.md`
- Blocked by `issues/008-tier2-builder-extension-features.md` (only if Tier-2 was pursued)

## User stories addressed

- User story 23
- User story 25
- User story 26
- User story 27
- User story 31
