## Parent PRD

`issues/prd.md`

## What to build

Tier-2 features that need horse-stats builder extensions — pursued only if approved in 003.
Extend the horse-stats builder to emit `LastRaceHeadGear` and `LastRaceJockeyId`, and
course/going/distance-conditioned prior-form aggregates, all via the leak-free as-of-date
pattern; regenerate `Horse_Stats.csv`. Derive first-time/changed-headgear, same-jockey-as-last-run,
and conditioned-form features. Tests including a leak-safety assertion. See the PRD "Second-tier
builder extensions".

## Acceptance criteria

- [ ] `Horse_Stats` gains `LastRaceHeadGear` and `LastRaceJockeyId`; first-time/changed-headgear and same-jockey flags are available as features.
- [ ] Course/going/distance-conditioned prior-form aggregates are computed and joined for prediction.
- [ ] A leak-safety test asserts the conditioned aggregates exclude the current race (mirroring the proxy-TSR as-of-date tests).
- [ ] `Horse_Stats.csv` regenerates and a short eval run uses the new features.

## Blocked by

- Blocked by `issues/005-tier1-features-new-card-columns.md`
- Conditional on the Tier-2 go/no-go recorded in `issues/003-review-approve-rules-and-features.md`

## User stories addressed

- User story 21
- User story 22
- User story 34

---

## Closure record (2026-06-05)

**Decision: Won't do — no-go confirmed.**

Issue 003 recorded a no-go on Tier-2 builder extensions: "The two approved rules already push
ROI into positive territory at 73.7% coverage. Adding horse-stats builder complexity introduces
data-pipeline risk and regeneration cost. Revisit only if the 009 final re-eval shows the gains
are insufficient."

Issue 009 (2026-06-05) showed all three acceptance-bar checks PASSED for the AbstainWrapper:
ROI-vs-coverage frontier dominates baseline at 72.9% coverage, gain stable across early-vs-late
split, and production anchor sanity check passed. The gains from Tier-1 features + abstain layer
are sufficient; the condition for revisiting Tier-2 did not materialise.

This issue is closed as **won't do** at this stage. If future evaluation shows further ROI
headroom worth pursuing, it remains a candidate for a new PRD.
