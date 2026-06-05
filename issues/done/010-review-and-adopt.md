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

- [x] An adoption decision is recorded explicitly against the acceptance bar.
- [x] If adopted: `ACTIVE_ALGORITHM` points to the new abstain wrapper; `predict.py` abstains in production consistently with eval; `evaluations.md` and memory are updated with honest frontier + coverage numbers.
- [ ] If not adopted: the rationale is recorded and the current baseline remains active.
- [x] A final confirmation that no shipped feature/filter input derives from odds.

## Blocked by

- Blocked by `issues/009-final-reeval-comparison-report.md`

## User stories addressed

- User story 3
- User story 28
- User story 29
- User story 30
- User story 31

---

## Adoption decision (2026-06-05)

**ADOPTED.** All three acceptance bar checks PASSED (from issue 009):

1. **ROI-vs-coverage frontier:** AbstainWrapper −£62 vs ProxyTSR −£117 at 72.9% coverage (+£55
   gain at same bet count, well above the 50% floor). PASSED.
2. **Early-vs-late stability:** AbstainWrapper ROI improves in the more recent period (−20 vs
   −42); gain is not an early-window artifact. PASSED.
3. **Production anchor:** AbstainWrapper 0.299 accuracy is +3.4 pp above the 0.265 live anchor —
   consistent and believable. PASSED.
4. **Odds safety:** confirmed clean. No feature or filter input derives from odds. PASSED.

**Changes made:**
- `race_analytics/algorithms/__init__.py`: `ACTIVE_ALGORITHM = ALGORITHMS[6]` (AbstainWrapperAlgorithm)
- `evaluations.md`: rewritten with honest frontier numbers (0.299 / −£62 / 72.9% / 1,699 bets),
  ROI-vs-coverage frontier table, early-vs-late stability table, updated active algorithm section
- Memory (`project_roi_abstain_features_prd.md`, `project_ratings_leakage.md`, `MEMORY.md`): updated

**predict.py production abstain check:** `predict.py` calls `algorithm.predict(card, ...)` where
`algorithm = ACTIVE_ALGORITHM = AbstainWrapperAlgorithm`. The abstain layer lives entirely inside
`AbstainWrapperAlgorithm.predict()` — it fires automatically in production with no additional
wiring change needed. Production abstains the same way evaluation does. ✓
