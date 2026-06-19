"""
Diagnostic staking backtest: replay the production staking module over the saved
walk-forward evaluation results.

⚠️  SP-PLACEHOLDER / DIAGNOSTIC-ONLY / NOT A PROMOTION DECISION  ⚠️
Forecast-price capture is forward-only and began ~2026-06, so the historical
``evaluation_results_*.csv`` carry ~0% real forecast coverage: their ``MarketProb``
and ``ResolvedOdds`` are SP-derived. This backtest therefore measures the *mechanics*
of the staking plan against an SP placeholder, NOT real forecast-time profitability.
It cannot move ``ACTIVE_ALGORITHM``. See ``evaluations.md`` and ``docs/data-pitfalls.md``.

Usage:
    python -m race_analytics.scripts.backtest_staking
    python -m race_analytics.scripts.backtest_staking path/to/evaluation_results_YYYYMMDD.csv
"""

import argparse
import glob
import os

import pandas as pd

from race_analytics.betting.staking import (
    MARKET_PROB,
    RESOLVED_ODDS,
    WIN_PROBABILITY,
    compute_stakes,
)

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_SCRIPTS_DIR))

_STAKE = "Stake"
# Columns compute_stakes needs; legacy eval files (pre-MarketProb) lack some of them.
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


def _numeric(values: pd.Series) -> pd.Series:
    """Coerce a column to float, turning unparseable / missing entries into NaN."""
    return pd.to_numeric(values, errors="coerce")  # pyright: ignore[reportReturnType]  # Series in -> Series out


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


def _attach_stakes(df: pd.DataFrame) -> pd.DataFrame:
    """Add a ``Stake`` column via the production ``compute_stakes``.

    Stakes are computed WITHIN each algorithm's full field: the production
    ``compute_stakes`` normalizes ``WinProbability`` within each ``RaceId``, and since
    every algorithm predicts the same races a shared ``RaceId`` would otherwise pool
    probabilities across algorithms. Computing per algorithm keeps each normalization to
    one model's field, exactly as the live predict step does.
    """
    out = df.reset_index(
        drop=True
    ).copy()  # unique labels: stacked eval files may collide
    out[_STAKE] = 0.0
    if not _STAKING_INPUTS.issubset(out.columns):
        return out  # legacy eval file (pre-MarketProb) -> nothing to stake, never a bet
    for _, idx in out.groupby("Algorithm", sort=False).groups.items():
        out.loc[idx, _STAKE] = compute_stakes(out.loc[idx]).to_numpy()
    return out


def _identify_picks(df: pd.DataFrame) -> pd.DataFrame:
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


def _summarise(picks: pd.DataFrame) -> dict[str, float]:
    """Kelly-staked vs flat-£1 performance, coverage, and the stake distribution.

    ``picks`` is one rank-1 pick per race carrying its advised ``Stake`` (from
    ``_attach_stakes``). Only settleable picks (a positive resolved price) are scored, so
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
    stake = settled[_STAKE]

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


def _backtest(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Per-algorithm staking summary over the evaluation results."""
    picks = _identify_picks(_attach_stakes(df))
    if picks.empty:
        return {}
    return {
        str(algo): _summarise(grp)
        for algo, grp in picks.groupby("Algorithm", sort=True)
    }


# ── I/O + display ──────────────────────────────────────────────────────────────

_CAVEAT = (
    "  SP-PLACEHOLDER / DIAGNOSTIC-ONLY / NOT A PROMOTION DECISION\n"
    "  Historical eval results carry ~0% real forecast prices, so MarketProb and\n"
    "  ResolvedOdds are SP-derived. This measures the staking plan's MECHANICS\n"
    "  against an SP placeholder, NOT real forecast-time profitability, and cannot\n"
    "  move ACTIVE_ALGORITHM. See evaluations.md / docs/data-pitfalls.md."
)


def _resolve_default_path() -> str | None:
    """Newest ``evaluation_results_*.csv`` in the repo root (date-stamped names sort)."""
    matches = sorted(glob.glob(os.path.join(_REPO_ROOT, "evaluation_results_*.csv")))
    return matches[-1] if matches else None


def _fmt(value: float) -> str:
    return "n/a" if pd.isna(value) else f"{value:.3f}"


def _print_summary(algo: str, s: dict[str, float]) -> None:
    print(f"\n{'=' * 70}")
    print(f"Algorithm: {algo}")
    print("=" * 70)
    print(f"  Races (settleable picks) : {int(s['races'])}")
    print(
        f"  Bets placed              : {int(s['bets'])}"
        f"   (coverage {s['coverage'] * 100:.1f}%)"
    )
    print(
        f"  Flat-£1 ROI              : {_fmt(s['flat_roi'])} per £1"
        f"   (net £{s['flat_profit']:+.2f})"
    )
    print(
        f"  Kelly-staked ROI         : {_fmt(s['kelly_roi'])} per £1"
        f"   (net £{s['kelly_profit']:+.2f})"
    )
    if int(s["bets"]) == 0:
        print("  Stake distribution       : no bets cleared the value gate")
        return
    print("  Stake distribution (£, over placed bets):")
    print(
        f"    min={_fmt(s['stake_min'])}  p10={_fmt(s['stake_p10'])}"
        f"  p25={_fmt(s['stake_p25'])}  median={_fmt(s['stake_median'])}"
    )
    print(
        f"    mean={_fmt(s['stake_mean'])}  p75={_fmt(s['stake_p75'])}"
        f"  p90={_fmt(s['stake_p90'])}  max={_fmt(s['stake_max'])}"
    )


def analyse(eval_csv_path: str) -> None:
    print("!" * 70)
    print(_CAVEAT)
    print("!" * 70)
    print(f"\nLoading eval results: {eval_csv_path}")
    df = pd.read_csv(eval_csv_path)
    print(
        f"  {len(df)} rows | {df['Algorithm'].nunique()} algo(s)"
        f" | {df['RaceId'].nunique()} unique races"
    )

    summaries = _backtest(df)
    if not summaries:
        print("\nNo picks could be identified (no scored rows).")
    for algo in sorted(summaries):
        _print_summary(algo, summaries[algo])

    print("\n" + "!" * 70)
    print(_CAVEAT)
    print("!" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Diagnostic staking backtest over saved evaluation results."
    )
    parser.add_argument(
        "eval_csv",
        nargs="?",
        default=None,
        help="Path to an evaluation_results_*.csv (default: newest in the repo root)",
    )
    args = parser.parse_args()
    path = args.eval_csv or _resolve_default_path()
    if path is None:
        parser.error(
            "no evaluation_results_*.csv found in the repo root; pass one explicitly"
        )
    analyse(path)
