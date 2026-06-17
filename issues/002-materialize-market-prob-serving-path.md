## Parent PRD

`issues/prd.md` — "Materialize in two non-shared places" (place **b**) and
"Odds columns must survive into the card subsets" (Implementation Decisions).

## What to build

Make the canonical serving transform chain produce `MarketProb`, covering **both** eval
serving and production serving through one code path.

- Add a `calculate_market_prob` transform (calls the `issues/001` helper) and append it
  to `CANONICAL_TRANSFORMS` in `race_analytics/features/race_data.py`, so every
  `RaceDataBuilder.build_serving*` output carries `MarketProb`.
- Retain the decimal-odds column(s) in the serving-card column selections so the
  transform has its input at serve time:
  - production card columns in `race_analytics/scripts/predict.py` (`_RACE_CARD_COLS`),
  - the eval `race_card` projection in `race_analytics/features/race_history.py`
    (`_RACE_CARD_COLS`).
  Carry `DecimalOdds` and `ForecastDecimalOdds` (the latter only when present — selections
  already filter `if c in columns`, so absence is graceful).

On the live card the morning forecast already occupies `DecimalOdds`, so production
naturally serves the forecast-derived `MarketProb` with no SP involved.

## Acceptance criteria

- [ ] `python -m race_analytics.scripts.predict` produces a serving frame whose runners
      carry a dense `MarketProb` column derived from the card's `DecimalOdds` (forecast).
- [ ] `calculate_market_prob` is the last/appropriate link in `CANONICAL_TRANSFORMS` and
      delegates to the `issues/001` helper (no duplicated coalesce/normalize logic).
- [ ] A test asserts `calculate_market_prob` produces the column on a **card-shaped**
      frame (forecast in `DecimalOdds` only) — per the PRD Testing Decisions.
- [ ] Existing predict/eval smoke paths still run; predicted population is unchanged.

## Blocked by

- Blocked by `issues/001-market-prob-resolver-helper.md`

## User stories addressed

- User story 7 (feature materialized on the serving path)
- User story 8 (production predictions use the morning forecast price for `MarketProb`)
