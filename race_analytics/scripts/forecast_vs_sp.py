"""
Compare the morning betting-forecast odds (ForecastDecimalOdds) against the
post-race SP (DecimalOdds) in the results files, for runners where both prices
are present and the runner completed the race.

Forecast capture is forward-only and began ~2026-06 (MarketProb PRD), so this
report grows as more race days accumulate. Re-run it periodically to confirm the
forecast<->SP relationship is stable before leaning on forecast-derived
MarketProb. See issues/todo.md for the recommended recheck cadence.

Usage:
    python -m race_analytics.scripts.forecast_vs_sp
    python -m race_analytics.scripts.forecast_vs_sp --data-dir path/to/Data
"""

import argparse
import glob
import os

import numpy as np
import pandas as pd

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)), "Data")


# ── I/O ─────────────────────────────────────────────────────────────────────


def _load_comparable(data_dir: str) -> pd.DataFrame:
    """Every completed runner that carries BOTH a forecast price and an SP.

    Returns one row per (RaceId, HorseId) with the two decimal prices, the race
    day, and the finishing position. Rows missing either price, or that did not
    complete the race, are dropped (an unpopulated forecast cell is the common case
    pre-2026-06, and SP is absent for non-runners / voids).
    """
    want = [
        "RaceId",
        "HorseId",
        "Off",
        "ResultStatus",
        "FinishingPosition",
        "DecimalOdds",
        "ForecastDecimalOdds",
    ]
    frames = []
    for path in sorted(glob.glob(os.path.join(data_dir, "Results_*.csv"))):
        df = pd.read_csv(path, usecols=lambda c: c in want)
        if "ForecastDecimalOdds" not in df.columns:
            continue  # legacy file written before the forecast columns existed
        frames.append(df)

    if not frames:
        return pd.DataFrame(columns=want)

    df = pd.concat(frames, ignore_index=True)
    df["DecimalOdds"] = pd.to_numeric(df["DecimalOdds"], errors="coerce")
    df["ForecastDecimalOdds"] = pd.to_numeric(
        df["ForecastDecimalOdds"], errors="coerce"
    )
    df = df[
        (df["ResultStatus"] == "CompletedRace")
        & df["DecimalOdds"].notna()
        & df["ForecastDecimalOdds"].notna()
        & (df["DecimalOdds"] > 0)
        & (df["ForecastDecimalOdds"] > 0)
    ].copy()
    df["Day"] = df["Off"].str.slice(0, 10)
    return df


# ── Pure helpers ──────────────────────────────────────────────────────────────


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 2 or x.std() == 0 or y.std() == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def _spearman(x: pd.Series, y: pd.Series) -> float:
    return _pearson(x.rank().to_numpy(), y.rank().to_numpy())


def _correlations(df: pd.DataFrame) -> dict[str, float]:
    f = df["ForecastDecimalOdds"]
    s = df["DecimalOdds"]
    fa = f.to_numpy()
    sa = s.to_numpy()
    return {
        "pearson_decimal": _pearson(fa, sa),
        "pearson_log": _pearson(np.log(fa), np.log(sa)),
        "pearson_impliedprob": _pearson(1 / fa, 1 / sa),
        "spearman_pooled": _spearman(f, s),
    }


def _per_race_agreement(df: pd.DataFrame) -> dict[str, float]:
    """Within-race agreement: rank correlation, favourite match, top-3 overlap."""
    rank_corrs = []
    fav_matches = 0
    races = 0
    top3_overlap = 0
    top3_slots = 0
    for _, race in df.groupby("RaceId", sort=False):
        if len(race) < 2:
            continue
        races += 1
        rc = _spearman(race["ForecastDecimalOdds"], race["DecimalOdds"])
        if not np.isnan(rc):
            rank_corrs.append(rc)
        fav_f = race.loc[race["ForecastDecimalOdds"].idxmin(), "HorseId"]
        fav_s = race.loc[race["DecimalOdds"].idxmin(), "HorseId"]
        fav_matches += int(fav_f == fav_s)
        n3 = min(3, len(race))
        f3 = set(race.nsmallest(n3, "ForecastDecimalOdds")["HorseId"])
        s3 = set(race.nsmallest(n3, "DecimalOdds")["HorseId"])
        top3_overlap += len(f3 & s3)
        top3_slots += len(f3)
    return {
        "races": races,
        "mean_per_race_rank_corr": float(np.mean(rank_corrs))
        if rank_corrs
        else float("nan"),
        "favourite_match_rate": fav_matches / races if races else float("nan"),
        "top3_overlap_rate": top3_overlap / top3_slots if top3_slots else float("nan"),
    }


def _differences(df: pd.DataFrame) -> dict[str, float]:
    f = df["ForecastDecimalOdds"]
    s = df["DecimalOdds"]
    abs_diff = (f - s).abs()
    rel_diff = abs_diff / s
    ratio = f / s
    return {
        "abs_diff_median": float(abs_diff.median()),
        "abs_diff_mean": float(abs_diff.mean()),
        "rel_diff_median": float(rel_diff.median()),
        "rel_diff_mean": float(rel_diff.mean()),
        "within_10pct": float((rel_diff <= 0.10).mean()),
        "within_25pct": float((rel_diff <= 0.25).mean()),
        "within_50pct": float((rel_diff <= 0.50).mean()),
        "ratio_median": float(ratio.median()),
        "shorter_rate": float((ratio < 0.95).mean()),  # forecast shorter than SP
        "same_rate": float(((ratio >= 0.95) & (ratio <= 1.05)).mean()),
        "longer_rate": float((ratio > 1.05).mean()),
    }


# ── Display ────────────────────────────────────────────────────────────────────


def analyse(data_dir: str) -> None:
    print(f"Scanning results files in: {data_dir}")
    df = _load_comparable(data_dir)
    if df.empty:
        print(
            "No comparable runners found (need both ForecastDecimalOdds and DecimalOdds).\n"
            "Forecast capture began ~2026-06 and is forward-only, so this is expected\n"
            "until validate has merged a few days of forecast prices into the results."
        )
        return

    by_day = df.groupby("Day").size().sort_index()
    print(f"\nComparable runners (forecast & SP both present, completed): {len(df)}")
    print(
        f"Race days covered: {len(by_day)}  ({by_day.index.min()} -> {by_day.index.max()})"
    )
    print("Runners per day:")
    for day, n in by_day.items():
        print(f"  {day}: {n}")

    corr = _correlations(df)
    print("\n--- Strength of relationship (higher = more similar ordering) ---")
    print(
        f"  Pearson r, raw decimal odds : {corr['pearson_decimal']:.3f}  (longshot-dominated)"
    )
    print(f"  Pearson r, log decimal odds : {corr['pearson_log']:.3f}")
    print(f"  Pearson r, implied prob 1/d : {corr['pearson_impliedprob']:.3f}")
    print(f"  Spearman rank r (pooled)    : {corr['spearman_pooled']:.3f}")

    agree = _per_race_agreement(df)
    print("\n--- Within-race agreement ---")
    print(f"  Races compared                       : {int(agree['races'])}")
    print(
        f"  Mean per-race rank correlation       : {agree['mean_per_race_rank_corr']:.3f}"
    )
    print(
        f"  Forecast favourite == SP favourite   : {agree['favourite_match_rate'] * 100:.0f}%"
    )
    print(
        f"  Forecast top-3 still in SP top-3     : {agree['top3_overlap_rate'] * 100:.0f}%"
    )

    diff = _differences(df)
    print("\n--- Per-runner price difference ---")
    print(
        f"  |forecast - SP| decimal : median={diff['abs_diff_median']:.2f}  mean={diff['abs_diff_mean']:.2f}"
    )
    print(
        f"  relative |F-SP| / SP    : median={diff['rel_diff_median'] * 100:.0f}%  mean={diff['rel_diff_mean'] * 100:.0f}%"
    )
    print(
        f"  within  10%={diff['within_10pct'] * 100:.0f}%"
        f"   25%={diff['within_25pct'] * 100:.0f}%"
        f"   50%={diff['within_50pct'] * 100:.0f}%"
    )

    print("\n--- Directional bias (forecast vs SP) ---")
    print(
        f"  Median ratio forecast/SP : {diff['ratio_median']:.3f}  (<1 = forecast typically shorter than SP)"
    )
    print(
        f"  Forecast shorter={diff['shorter_rate'] * 100:.0f}%"
        f"   ~same={diff['same_rate'] * 100:.0f}%"
        f"   longer={diff['longer_rate'] * 100:.0f}%"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compare forecast odds vs post-race SP in the results files."
    )
    parser.add_argument(
        "--data-dir",
        default=_DATA_DIR,
        help=f"Directory holding Results_*.csv (default: {_DATA_DIR})",
    )
    args = parser.parse_args()
    analyse(args.data_dir)
