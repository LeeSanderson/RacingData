"""Pure, dependency-free staking math and its backtest summarization.

The deep, isolated core of the advisory-``Stake`` feature (``issues/prd.md``): it holds
the staking math and the functions that summarise its return over saved evaluation
results, and nothing else — no I/O, no pipeline coupling. Everything operates over a
*field* frame (one row per runner) carrying ``RaceId``, the model's un-normalized
``WinProbability``, the overround-removed ``MarketProb``, and a resolved gross decimal
odds column. Consumers — the predict step, the evaluator, and the diagnostic backtest —
call these functions rather than re-deriving the math.

Strategy: normalize each runner's ``WinProbability`` within its race into a true
``ModelProb``, judge value as ``edge = ModelProb - MarketProb``, and size a fraction of
the full Kelly stake when the edge clears ``MIN_EDGE``. The **gross-pay /
de-overround-judge split** is deliberate: the Kelly payout term uses the gross price
actually on offer (``O``), while the value gate uses the overround-removed ``MarketProb``,
so the bookmaker's margin is not double-counted against genuine value.

The summarization layer (``attach_stakes`` → ``identify_picks`` → ``summarise``, run
per algorithm by ``backtest``) replays this staking plan over an evaluation-results frame
to report Kelly-staked vs flat-£1 return, coverage, and the stake distribution.
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


STAKE = "Stake"
_STAKING_INPUTS = {WIN_PROBABILITY, MARKET_PROB, RESOLVED_ODDS}
_STAKE_DIST_FIELDS = (
    "stake_median",
    "stake_mean",
    "stake_p10",
    "stake_p25",
    "stake_p75",
    "stake_p90",
    "stake_min",
    "stake_max",
)


def _empty_summary() -> dict[str, float]:
    """Zeroed summary for an unbettable / empty field (no division by a zero stake)."""
    return {
        "races": 0,
        "flat_profit": 0.0,
        "flat_roi": 0.0,
        "bets": 0,
        "coverage": 0.0,
        "kelly_profit": 0.0,
        "kelly_roi": float("nan"),
        **{k: float("nan") for k in _STAKE_DIST_FIELDS},
    }


def attach_stakes(df: pd.DataFrame) -> pd.DataFrame:
    """Add a ``Stake`` column via ``compute_stakes``.

    Stakes are computed WITHIN each algorithm's full field: ``compute_stakes`` normalizes
    ``WinProbability`` within each ``RaceId``, and since every algorithm predicts the same
    races a shared ``RaceId`` would otherwise pool probabilities across algorithms.
    Computing per algorithm keeps each normalization to one model's field, exactly as the
    live predict step does.
    """
    out = df.reset_index(
        drop=True
    ).copy()  # unique labels: stacked eval files may collide
    out[STAKE] = 0.0
    if not _STAKING_INPUTS.issubset(out.columns):
        return out  # legacy eval file (pre-MarketProb) -> nothing to stake, never a bet
    for _, idx in out.groupby("Algorithm", sort=False).groups.items():
        out.loc[idx, STAKE] = compute_stakes(out.loc[idx]).to_numpy()
    return out


def identify_picks(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (FoldDate, Algorithm, RaceId): the rank-1 pick the model would bet.

    Picks the horse with the highest ``WinProbability`` (falling back to ``PredictedScore``
    for algorithms that emit no probability), mirroring the live predict step's
    ``PredictedRank == 1``. The selected row carries its already-attached ``Stake``.
    """
    group_keys = ["FoldDate", "Algorithm", "RaceId"]
    has_prob = "WinProbability" in df.columns
    has_score = "PredictedScore" in df.columns

    def pick_row(g: pd.DataFrame) -> pd.Series:
        if has_prob and g["WinProbability"].notna().any():
            return g.loc[g["WinProbability"].idxmax()]
        if has_score and g["PredictedScore"].notna().any():
            return g.loc[g["PredictedScore"].idxmax()]
        return g.iloc[0]

    return (
        df.groupby(group_keys, sort=False)
        .apply(pick_row, include_groups=False)
        .reset_index()
        .drop(columns=["level_3"], errors="ignore")
    )


def summarise(picks: pd.DataFrame) -> dict[str, float]:
    """Kelly-staked vs flat-£1 performance, coverage, and the stake distribution.

    ``picks`` is one rank-1 pick per race carrying its advised ``Stake`` (from
    ``attach_stakes``). Only settleable picks (a positive resolved price) are scored, so
    a winner can always be valued. The flat-£1 baseline bets £1 on every pick; the Kelly
    figure bets only the gated subset (``Stake > 0``). ROI is profit per £1 staked.

    Returns NaNs for the Kelly figures when nothing clears the value gate (no division by
    a zero stake), and zeros across the board for an empty field.
    """
    # ResolvedOdds is the price the live pipeline values winners at; on SP-only history
    # it equals DecimalOdds, so older eval files (no ResolvedOdds) settle on DecimalOdds.
    odds_col = RESOLVED_ODDS if RESOLVED_ODDS in picks.columns else "DecimalOdds"
    if picks.empty or odds_col not in picks.columns:
        return _empty_summary()

    odds = _numeric(picks[odds_col])
    mask = odds.notna() & (odds > 0)
    settled = picks[mask].copy()
    settled["ResolvedOdds"] = odds[mask]

    races = len(settled)
    if races == 0:
        return _empty_summary()

    won = settled["FinishingPosition"] == 1
    o = settled["ResolvedOdds"]
    stake = settled[STAKE]

    flat_profit = float((o - 1.0).where(won, -1.0).sum())
    flat_roi = flat_profit / races

    bet = stake > 0
    bets = int(bet.sum())
    coverage = bets / races

    staked = stake[bet]
    if bets == 0:
        kelly_profit = 0.0
        kelly_roi = float("nan")
        stake_dist = {k: float("nan") for k in _STAKE_DIST_FIELDS}
    else:
        kelly_profit = float((staked * (o[bet] - 1.0)).where(won[bet], -staked).sum())
        kelly_roi = kelly_profit / float(staked.sum())
        stake_dist = {
            "stake_median": float(staked.median()),
            "stake_mean": float(staked.mean()),
            "stake_p10": float(staked.quantile(0.10)),
            "stake_p25": float(staked.quantile(0.25)),
            "stake_p75": float(staked.quantile(0.75)),
            "stake_p90": float(staked.quantile(0.90)),
            "stake_min": float(staked.min()),
            "stake_max": float(staked.max()),
        }

    return {
        "races": races,
        "flat_profit": flat_profit,
        "flat_roi": flat_roi,
        "bets": bets,
        "coverage": coverage,
        "kelly_profit": kelly_profit,
        "kelly_roi": kelly_roi,
        **stake_dist,
    }


def backtest(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Per-algorithm staking summary over the evaluation results."""
    picks = identify_picks(attach_stakes(df))
    if picks.empty:
        return {}
    return {
        str(algo): summarise(grp) for algo, grp in picks.groupby("Algorithm", sort=True)
    }
