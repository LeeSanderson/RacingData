"""Pure, dependency-free staking math — fractional Kelly behind a value gate.

The deep, isolated core of the advisory-``Stake`` feature (``issues/prd.md``): it holds
the staking math and nothing else — no I/O, no pipeline coupling. Everything operates
over a *field* frame (one row per runner) carrying ``RaceId``, the model's un-normalized
``WinProbability``, the overround-removed ``MarketProb``, and a resolved gross decimal
odds column. Consumers — the predict step and the diagnostic backtest — call these
functions rather than re-deriving the math.

Strategy: normalize each runner's ``WinProbability`` within its race into a true
``ModelProb``, judge value as ``edge = ModelProb - MarketProb``, and size a fraction of
the full Kelly stake when the edge clears ``MIN_EDGE``. The **gross-pay /
de-overround-judge split** is deliberate: the Kelly payout term uses the gross price
actually on offer (``O``), while the value gate uses the overround-removed ``MarketProb``,
so the bookmaker's margin is not double-counted against genuine value.
"""

import pandas as pd

RACE_ID = "RaceId"
WIN_PROBABILITY = "WinProbability"
MARKET_PROB = "MarketProb"
RESOLVED_ODDS = "ResolvedOdds"

KELLY_FRACTION = 0.25  # fraction of full Kelly; the primary miscalibration buffer.
MIN_EDGE = 0.03
CAP = 5.0  # maximum single stake (£), bounding short-priced high-confidence tails.
# Calibrated so the median advised stake lands ≈ £1 (a fixed, stateless notional scale;
# no running-balance tracking). Re-derive if the stake distribution shifts.
BANKROLL = 120.0


def _numeric(values: pd.Series) -> pd.Series:
    """Coerce a column to float, turning unparseable / missing entries into NaN."""
    return pd.to_numeric(values, errors="coerce")  # pyright: ignore[reportReturnType]  # Series in -> Series out


def normalize_within_race(
    field: pd.DataFrame,
    prob_col: str = WIN_PROBABILITY,
    race_col: str = RACE_ID,
) -> pd.Series:
    """Normalize a per-horse probability within each race so each field sums to 1.

    Raw ``WinProbability`` is an un-normalized per-horse classifier output; dividing by
    the per-race total turns it into a true within-race distribution (``ModelProb``)
    directly comparable to the overround-removed ``MarketProb``. Races whose
    probabilities sum to 0 (or non-finite) yield NaN, which the stake gate treats as
    no-bet.
    """
    prob = _numeric(field[prob_col])
    race_total = prob.groupby(field[race_col]).transform("sum")
    return prob / race_total.where(race_total > 0)


def kelly_fraction(model_prob: pd.Series, odds: pd.Series) -> pd.Series:
    """Full Kelly fraction ``f* = (p·O - 1) / (O - 1)`` for gross decimal odds ``O``.

    ``p`` is the within-race-normalized model probability and ``O`` the gross price on
    offer. NaN where odds are missing or not greater than 1 (the divisor ``O - 1`` is
    then ≤ 0 / undefined); callers floor the result at 0 before staking.
    """
    return ((model_prob * odds - 1.0) / (odds - 1.0)).where(odds > 1.0)


def compute_stakes(
    field: pd.DataFrame,
    odds_col: str = RESOLVED_ODDS,
    prob_col: str = WIN_PROBABILITY,
    market_col: str = MARKET_PROB,
    race_col: str = RACE_ID,
    *,
    kelly_frac: float = KELLY_FRACTION,
    min_edge: float = MIN_EDGE,
    cap: float = CAP,
    bankroll: float = BANKROLL,
) -> pd.Series:
    """Advised stake per runner: fractional Kelly behind a value gate, capped.

    Returns a float Series of stakes aligned to ``field.index``, rounded to 2dp. A row
    stakes 0 unless its edge ``ModelProb - MarketProb`` strictly exceeds ``min_edge`` and
    its gross odds are present and greater than 1; otherwise it stakes
    ``min(kelly_frac · max(0, f*) · bankroll, cap)``. The Kelly payout term uses the
    gross odds while the value gate uses the overround-removed ``MarketProb`` (the
    gross-pay / de-overround-judge split).
    """
    model_prob = normalize_within_race(field, prob_col, race_col)
    market_prob = _numeric(field[market_col])
    odds = _numeric(field[odds_col])

    edge = model_prob - market_prob
    bet = (
        odds.notna()
        & (odds > 1.0)
        & model_prob.notna()
        & market_prob.notna()
        & (edge > min_edge)
    )

    f_star = kelly_fraction(model_prob, odds).clip(lower=0.0)
    stake = (kelly_frac * f_star * bankroll).where(bet, 0.0)
    return stake.clip(upper=cap).round(2)
