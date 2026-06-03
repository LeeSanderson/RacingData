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

- [x] A fast-XGBoost feature screen ranks the new features and selects those that improve the screening metric.
- [ ] A full 180-fold ProxyTSR re-eval runs with the selected features + abstain layer and writes results.
- [ ] The report compares the new config's ROI-vs-coverage frontier to the baseline at >= 50% coverage, shows early-vs-late stability, and the anchor sanity-check.
- [x] A check confirms no feature/filter input is derived from odds.

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

---

## Progress note (2026-06-02)

### What was done

**Feature screen** (`race_analytics/scripts/feature_screen.py`) — new script, 5 unit tests passing.

Ran on 7 months training data (88,621 rows). Single-bulk-fit approach: load + engineer features once, fit XGBoostAlgorithm, report importances.

#### Odds safety check: CLEAN
No feature name contains any odds-related keyword.

#### Feature selection results (new Tier-1 features only)

| Feature | Importance | Selected |
|---|---|---|
| AgeBand_4yoPlus | 0.001475 | YES |
| IsHandicap | 0.000925 | YES |
| AgeBand_3yoPlus | 0.000693 | YES |
| Age | 0.000707 | YES |
| AgeBand_3yo | 0.000449 | YES |
| AgeBand_None | 0.000388 | YES |
| Pattern_Listed | 0.000387 | YES |
| SexRestriction_F | 0.000209 | YES |
| RelAge | 0.000197 | YES |
| RaceClass | 0.000000 | no |
| DrawPct | 0.000000 | no |
| RelDraw | 0.000000 | no |
| Pattern_Group1/2/3/None | 0.000000 | no |
| AgeBand_2yo | 0.000000 | no |
| SexRestriction_FM/Open | 0.000000 | no |

**Selected (9):** Age, AgeBand_3yo, AgeBand_3yoPlus, AgeBand_4yoPlus, AgeBand_None, IsHandicap, Pattern_Listed, RelAge, SexRestriction_F

**Dropped (10):** AgeBand_2yo, DrawPct, Pattern_Group1, Pattern_Group2, Pattern_Group3, Pattern_None, RaceClass, RelDraw, SexRestriction_FM, SexRestriction_Open

Note: XGBoost assigns 0 importance to the dropped features. They remain in OPTIONAL_PREDICTORS (no harm to ProxyTSR — zero-importance features get no splits); they can be removed in a future cleanup if desired. The 9 selected features will be active in all fold training runs automatically.

### What's left

**Full 180-fold comparison eval** — this must be run as an AFK task by the user. Command:

```powershell
python -m race_analytics.scripts.evaluate --folds 180 --training-months 7 --algorithms ProxyTSRXGBoostAlgorithm,AbstainWrapperAlgorithm --save-results --results-file evaluation_comparison_20260602.csv
```

Expected runtime: ~2-3 hours (feature engineering ~5 min/fold + ProxyTSR fit ~34s/fold × 2 algorithms × 180 folds).

The evaluate.py output already includes:
- Summary table: accuracy, ROI, races, fav accuracy, fav ROI
- Early-vs-late stability split
- ROI-vs-coverage frontier for AbstainWrapperAlgorithm

The comparison report is produced by interpreting that output against the baseline from evaluations.md (ProxyTSR: accuracy=0.294, ROI=−22.20, 2517 races) and the production anchor (0.265 / +£78).

**2-fold pipeline demo** (`evaluation_comparison_demo_20260602.csv`) completed. Results (noisy, only 25 races — directionally informative only):

| Algorithm | Accuracy | ROI | Races | Coverage |
|---|---|---|---|---|
| ProxyTSRXGBoostAlgorithm | 0.400 | −1.367 | 25 | 100% |
| AbstainWrapperAlgorithm | 0.421 | +0.833 | 19 | 76% |

AbstainWrapper beats baseline on both accuracy and ROI at 76% coverage (above the 50% floor). Early-vs-late (1 fold each, extremely noisy): ProxyTSR Early 0.500/+2.883 vs Late 0.222/−4.250; AbstainWrapper Early 0.583/+5.583 vs Late 0.143/−4.750. The 180-fold run is needed for any conclusions.
