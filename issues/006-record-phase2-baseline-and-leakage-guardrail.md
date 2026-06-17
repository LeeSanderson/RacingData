# Record the Phase-2 baseline and leakage guardrail

## Parent PRD

`issues/prd-forecast-odds.md`

## What to build

A documentation/guardrail slice closing out the parts of the PRD that aren't code: recording the Phase 2 baseline and the leakage guardrail so the next implementer starts from a clear place and the known trap is not re-introduced. Best worked after the rest of Phase 1 has shipped.

1. **Phase 2 scope-out (user story 21):** Record that live / market odds (the Diffusion-fed "betting-odds" tab) are deferred to Phase 2, with its known blocker captured: the Puppeteer loader navigates with `GoToAsync` (load event) and immediately reads content, so the post-load live feed is not captured — Phase 2 needs a wait strategy / tab activation / odds endpoint plus an empirical check of *when* prices populate during the morning, and will add `Starting*` columns to both card and results. Use the PRD's "Out of Scope" and "Further Notes" sections as the source.
2. **Leakage guardrail (user story 15):** Record that the card now carries a real forecast price at prediction time, and that the forecast must **not** become a Python model feature/filter unless deliberately and safely introduced. The Python predictor currently ignores card odds, so no leakage occurs today — this must stay true.
3. **Follow-up note:** Revise the `project_odds_unavailable_at_prediction` understanding, which is now partially outdated: a forecast price now exists on the card at prediction time and must be kept out of features.

No production C# or Python behaviour changes in this slice.

## Acceptance criteria

- [ ] The Phase 2 baseline (live-odds scope + the `GoToAsync` loader blocker + planned `Starting*` columns) is recorded somewhere durable a future implementer will find (e.g. project docs / notes).
- [ ] The leakage guardrail (forecast price must not silently become a model feature) is recorded.
- [ ] The `project_odds_unavailable_at_prediction` understanding is updated to reflect that a real forecast price now exists on the card at prediction time.
- [ ] No change to runtime C#/Python behaviour.

## Blocked by

None - can start immediately (logically best done after the rest of Phase 1 ships).

## User stories addressed

Reference by number from the parent PRD:

- User story 15
- User story 21
