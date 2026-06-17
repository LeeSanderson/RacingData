## Parent PRD

`issues/prd.md` — "Guardrail docs and memory updated" (Implementation Decisions),
plus the leakage-rule reasoning in "Further Notes".

## What to build

Update the leakage guardrails so the docs do not contradict the code now that
`MarketProb` is a deliberately sanctioned feature.

- `docs/data-pitfalls.md` — Pitfall 2: record that `MarketProb` (forecast-derived,
  SP-fallback) is now a **deliberately sanctioned** model feature that consciously clears
  "bar 2" for the forecast price, while the post-race **SP remains barred as a direct
  feature** and the SP fallback is a transitional placeholder. Keep the two-bar framing
  intact.
- `docs/odds-capture.md` — revise the Phase 1 "Leakage guardrail" note: the forecast is
  no longer ignored by the predictor; it now feeds `MarketProb` through the resolver,
  evaluated honestly, with the SP fallback retiring itself as coverage accrues.
- The odds memory note (`project_odds_unavailable_at_prediction`): update to reflect that
  `MarketProb` is a sanctioned feature with a forecast-vs-SP caveat.
- State (in the docs and/or memory) that a fully forecast-fed training window will not
  exist for months, so the re-eval threshold is chosen with that reality in mind rather
  than a hard-coded date.

## Acceptance criteria

- [ ] `docs/data-pitfalls.md` Pitfall 2 states `MarketProb` is sanctioned, SP fallback is
      transitional, post-race SP stays barred as a direct feature — two-bar framing intact.
- [ ] `docs/odds-capture.md` Phase 1 guardrail note no longer says the predictor ignores
      card odds; it describes the `MarketProb` resolver path.
- [ ] The odds memory note is updated to match (sanctioned feature + forecast-vs-SP caveat).
- [ ] The "fully forecast-fed window is months away" reality is recorded where the re-eval
      threshold is discussed.

## Blocked by

- Blocked by `issues/004-expose-market-prob-optional-predictors.md`

## User stories addressed

- User story 18 (guardrail docs + memory updated; odds now a sanctioned feature)
- User story 19 (known SP-vs-forecast divergence documented)
- User story 20 (PRD/docs state a fully forecast-fed window is months away)
