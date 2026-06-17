## Parent PRD

`issues/prd.md` — "Measurement sourced through the same resolver" (Implementation
Decisions), "Test the measurement change in isolation" (Testing Decisions).

## What to build

Make the evaluation's **measurement** constructs source odds through the same resolution
rule as the model (forecast → SP), so the baseline and the feature use a consistent
notion of "the market". Under the stated forecast ≈ SP assumption this is a **no-op on
historic SP-only data** and only begins to diverge as forecast coverage accrues.

- ROI valuation (`race_analytics/utils/scoring.py::roi`) values winning bets at the
  **resolved** decimal odds (forecast-when-present-else-SP), reusing the resolved-odds
  output of the `issues/001` helper rather than reading `DecimalOdds` directly.
- The market-favourite baseline (`race_analytics/algorithms/market_favourite.py`) selects
  the morning favourite by **resolved** odds (lowest resolved decimal odds).
- Ensure the results frame the eval passes to these (`_results` in `evaluate.py`) carries
  the forecast odds column so the resolver has both inputs.

## Acceptance criteria

- [ ] `roi` values winners at resolved odds: forecast-present values at forecast,
      forecast-absent values at SP.
- [ ] `MarketFavouriteBaseline` picks the lowest **resolved** decimal-odds runner per race.
- [ ] Isolated tests on small synthetic frames confirm: forecast-present → forecast value;
      forecast-absent → SP value; **historic SP-only data is unchanged** (regression guard
      that today's numbers do not move).

## Blocked by

- Blocked by `issues/001-market-prob-resolver-helper.md`

## User stories addressed

- User story 11 (ROI values winning bets at resolved odds)
- User story 12 (market-favourite baseline picks favourite by resolved odds)
