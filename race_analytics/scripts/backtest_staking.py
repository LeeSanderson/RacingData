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

from race_analytics.betting import backtest

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_SCRIPTS_DIR))


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

    summaries = backtest(df)
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
