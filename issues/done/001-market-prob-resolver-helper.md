## Parent PRD

`issues/prd.md` — "One odds resolver / `MarketProb` helper" (Implementation Decisions),
"Extract pure functions and unit-test them" (Testing Decisions).

## What to build

A single pure function (Python, in `race_analytics/features/`) that owns the entire
market-odds rule end-to-end over a race frame. It is the **only** place the coalesce
and the normalization live. Given a frame (one row per runner, grouped by `RaceId`) it:

1. Resolves each runner's **decimal odds** as forecast-when-present-else-SP — i.e.
   coalesce `ForecastDecimalOdds` → `DecimalOdds`. Expose this resolved-odds value as a
   reusable output, because the measurement slice (`issues/005-*`) needs the resolved
   decimal odds, not the probability.
2. Converts resolved odds to an implied probability (`1 / decimal`).
3. Normalizes within each race so `MarketProb` sums to 1 per `RaceId` (removes the
   bookmaker overround → a true probability comparable to the model's `WinProbability`).
4. Falls back to a **uniform prior** (`1 / field size`) when odds are missing or the
   runner is void / non-completing, so the column is dense (never NaN) and linear models
   (Ridge) do not break.

This slice delivers the helper **and its unit tests only** — it is not yet wired into
any transform chain or consumer (those are `issues/002`–`issues/006`). It is the
foundation those slices build on. Demoable via the test suite.

## Acceptance criteria

- [ ] A pure helper exists in `race_analytics/features/` that takes a race frame and
      returns it with a dense `MarketProb` column (no NaN), and exposes the resolved
      decimal-odds coalesce as a reusable function/output.
- [ ] Unit tests (in `tests/features/`, mirroring the package per repo convention) cover:
      forecast-present uses forecast; forecast-absent falls back to SP; per-race
      normalization sums to 1.0; missing/void odds resolve to the uniform prior
      (`1 / field size`); a full multi-runner race produces the expected probabilities.
- [ ] No existing pipeline behaviour changes (helper is not yet wired in) — full test
      suite still green.

## Blocked by

None - can start immediately.

## User stories addressed

- User story 1 (market-implied win probability available as a feature)
- User story 2 (derived forecast-else-SP through one resolver)
- User story 3 (resolver prefers forecast automatically; SP fallback self-retires)
- User story 4 (`MarketProb` normalized within race to sum to 1)
- User story 5 (missing/void odds → uniform prior, never NaN)
