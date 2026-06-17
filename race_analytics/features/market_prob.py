"""Market-implied win probability (`MarketProb`) — the single home of the odds rule.

This module owns the entire market-odds feature end-to-end and is the ONLY place the
forecast/SP coalesce and the per-race normalization live:

  1. Resolve each runner's decimal odds as forecast-when-present-else-SP
     (coalesce ``ForecastDecimalOdds`` -> ``DecimalOdds``).
  2. Convert to an implied probability (``1 / decimal``).
  3. Normalize within each ``RaceId`` so ``MarketProb`` sums to 1 (removes the
     bookmaker overround -> a true probability comparable to ``WinProbability``).
  4. Fall back to a uniform prior (``1 / field size``) when a runner's resolved odds
     are missing or non-positive (void / non-completing), so the column stays dense
     (never NaN) and linear models (Ridge) do not break.

Consumers — the canonical serving transform chain, the harness training path, and the
eval measurement slice (ROI / favourite baseline) — all call ``resolve_decimal_odds`` /
``add_market_prob`` rather than re-deriving the rule.
"""

import numpy as np
import pandas as pd

MARKET_PROB = "MarketProb"
_FORECAST_ODDS = "ForecastDecimalOdds"
_DECIMAL_ODDS = "DecimalOdds"


def _odds_column(races: pd.DataFrame, name: str) -> pd.Series:
    if name in races.columns:
        return pd.to_numeric(races[name], errors="coerce")  # pyright: ignore[reportReturnType]  # to_numeric returns a Series for a Series input
    return pd.Series(np.nan, index=races.index, dtype=float)


def resolve_decimal_odds(races: pd.DataFrame) -> pd.Series:
    """Resolve each runner's decimal odds as forecast-when-present-else-SP.

    Coalesces ``ForecastDecimalOdds`` -> ``DecimalOdds`` into a float Series aligned to
    ``races.index``. The forecast is preferred wherever present, so the SP fallback
    retires itself as forecast coverage accrues. Non-positive prices are not real quotes
    and resolve to NaN. Graceful when either column is absent. This is the reusable
    coalesce the measurement slice consumes directly.
    """
    forecast = _odds_column(races, _FORECAST_ODDS)
    sp = _odds_column(races, _DECIMAL_ODDS)
    resolved = forecast.where(forecast.notna(), sp)
    return resolved.where(resolved > 0).astype(float)


def add_market_prob(races: pd.DataFrame) -> pd.DataFrame:
    """Return ``races`` with a dense ``MarketProb`` column (never NaN).

    Resolves odds (forecast -> SP), converts to an implied probability, and normalizes
    within each ``RaceId`` so the field sums to 1. A runner whose resolved odds are
    missing/non-positive takes the uniform prior (``1 / field size``) as its implied
    probability before normalization; when a whole race is unpriced every runner
    resolves to exactly ``1 / field size``.
    """
    races = races.copy()
    if "RaceId" in races.columns:
        race_key = races["RaceId"]
    else:
        race_key = pd.Series(0, index=races.index)
    field_size = race_key.groupby(race_key).transform("size")
    uniform_prior = 1.0 / field_size

    implied = 1.0 / resolve_decimal_odds(races)
    implied = implied.where(implied.notna(), uniform_prior)

    race_total = implied.groupby(race_key).transform("sum")
    races[MARKET_PROB] = implied / race_total
    return races
