## Parent PRD

`issues/prd.md`

## What to build

Human review of the diagnostic output from 002. Approve a short list of **2-4 hard-race rules**
to implement (each justified as both intuitive and stable across the window), and make the
**go/no-go decision on the Tier-2 builder-extension features** (008). Record the approved rules in
a form the Filter B slice (007) can consume directly. This is the HITL half of the diagnostic.
See the PRD "Filter B" and the Workstream 2 tiering notes.

## Acceptance criteria

- [x] 2-4 hard-race rules are selected from the diagnostic's candidate list, each with a recorded justification (intuitive + stable).
- [x] A recorded go/no-go decision on whether Tier-2 features (008) are worth building.
- [x] The approved rules are written down (in this issue or a linked note) precisely enough for 007 to implement without re-deriving them.

## Blocked by

- Blocked by `issues/002-diagnostic-analysis-script.md`

## User stories addressed

- User story 12

---

## Decision record (2026-06-02)

Diagnostic run: 30-fold walk-forward on ProxyTSRXGBoostAlgorithm, 471 picks.
Baseline: 28.0% win rate, ROI -0.093.

### Approved hard-race rules for issue 007

**Rule A — Exclude sprint races (distance < 6 furlongs)**
- Justification: <6f segment ROI -0.559 (worst of any distance band); sprint form is volatile
  and hard to model without draw/going-bias/track-camber data we don't have. Intuitive and
  stable — short-distance races reward specialist knowledge the model lacks.
- Impact alone: 396 bets kept (84.1% coverage), ROI -0.004 (+0.088 delta).

**Rule B — Exclude Class 6 races**
- Justification: lowest-grade races (selling/claiming) have inconsistent form lines and
  erratic odds. Class 6 ROI -0.315 vs baseline -0.093. Intuitive: weakest horses run
  unpredictably. Coverage impact is small (14.2% excluded).
- Impact alone: 404 bets kept (85.8% coverage), ROI -0.056 (+0.037 delta).

**Combined (Rules A + B):**
- 347 bets kept, **73.7% coverage** (well above 50% floor).
- ROI **+0.011** (baseline -0.093 → delta +0.104).
- Adding a field-size cap (>8) on top hurt the combined ROI (-0.042 vs +0.011) so it was rejected.

### Tier-2 features decision (issue 008)

**No-go on Tier-2 builder extensions** at this stage. The two approved rules already push ROI
into positive territory at 73.7% coverage. Adding horse-stats builder complexity introduces
data-pipeline risk and regeneration cost. Revisit only if the 009 final re-eval shows the
gains are insufficient.

Issue 008 remains open but deprioritised; it should not block 009.
