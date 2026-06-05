"""
Diagnostic analysis: characterise when the model wins and loses.
Usage: python -m race_analytics.scripts.diagnostic path/to/eval_results.csv
"""
import argparse
import glob
import os

import numpy as np
import pandas as pd

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)), "Data")

_FURLONG_M = 201.168


# ── Pure helpers ──────────────────────────────────────────────────────────────

def _distance_band(meters: float) -> str:
    if pd.isna(meters):
        return "Unknown"
    furlongs = meters / _FURLONG_M
    if furlongs < 6:
        return "<6f"
    elif furlongs < 8:
        return "6-8f"
    elif furlongs < 10:
        return "8-10f"
    elif furlongs < 12:
        return "10-12f"
    elif furlongs < 16:
        return "12-16f"
    else:
        return "16f+"


def _field_size_band(n: float) -> str:
    if pd.isna(n):
        return "Unknown"
    n = int(n)
    if n <= 5:
        return "2-5"
    elif n <= 8:
        return "6-8"
    elif n <= 12:
        return "9-12"
    elif n <= 16:
        return "13-16"
    else:
        return "17+"


def _identify_picks(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (FoldDate, Algorithm, RaceId): the horse with the highest score.

    Uses WinProbability if any non-NA value exists in the group, then falls
    back to PredictedScore, then takes the first row.
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


def _roi(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    wins = df["FinishingPosition"] == 1
    profit = (df.loc[wins, "DecimalOdds"] - 1).sum() - (~wins).sum()
    return float(profit / len(df))


def _segment_table(picks: pd.DataFrame, col: str) -> pd.DataFrame:
    total = len(picks)
    picks = picks.copy()
    picks["_win"] = (picks["FinishingPosition"] == 1).astype(int)
    picks["_profit"] = picks.apply(
        lambda r: float(r["DecimalOdds"] - 1) if r["_win"] else -1.0, axis=1
    )
    agg = picks.groupby(col, sort=False).agg(
        Bets=("_win", "count"),
        _wins=("_win", "sum"),
        _profit=("_profit", "sum"),
    ).reset_index()
    agg["WinRate"] = agg["_wins"] / agg["Bets"]
    agg["ROI"] = agg["_profit"] / agg["Bets"]
    agg["Coverage"] = agg["Bets"] / total
    return agg[[col, "Bets", "WinRate", "ROI", "Coverage"]]


# ── I/O helpers ───────────────────────────────────────────────────────────────

def _load_results_extra(picks: pd.DataFrame) -> pd.DataFrame:
    """Join AgeBand, Pattern, RatingBand from the raw Results_*.csv files."""
    race_ids = set(picks["RaceId"].unique())
    want = {"RaceId", "AgeBand", "Pattern", "RatingBand", "SexRestriction"}
    dfs = []
    for path in sorted(glob.glob(os.path.join(_DATA_DIR, "Results_*.csv")), reverse=True):
        df = pd.read_csv(path, usecols=lambda c: c in want)
        df = df[df["RaceId"].isin(race_ids)].drop_duplicates("RaceId")
        if not df.empty:
            dfs.append(df)
        if dfs and set(pd.concat(dfs)["RaceId"].unique()) >= race_ids:
            break
    if not dfs:
        return picks
    extra = pd.concat(dfs).drop_duplicates("RaceId")
    return picks.merge(extra, on="RaceId", how="left")


# ── Display helpers ────────────────────────────────────────────────────────────

def _confidence_band(prob: float) -> str:
    if pd.isna(prob):
        return "NA"
    if prob < 0.15:
        return "<15%"
    elif prob < 0.20:
        return "15-20%"
    elif prob < 0.25:
        return "20-25%"
    elif prob < 0.30:
        return "25-30%"
    elif prob < 0.35:
        return "30-35%"
    else:
        return "35%+"


_BAND_ORDER = ["<15%", "15-20%", "20-25%", "25-30%", "30-35%", "35%+", "NA"]


def _print_segment_table(seg: pd.DataFrame, col: str, title: str) -> None:
    print(f"\n--- {title} ---")
    print(f"  {'Segment':<25} {'Bets':>6} {'WinRate':>8} {'ROI':>8} {'Coverage':>9}")
    print("  " + "-" * 60)
    for _, row in seg.sort_values("ROI", ascending=False).iterrows():
        print(
            f"  {str(row[col]):<25} {int(row['Bets']):>6} {row['WinRate']:>8.3f}"
            f" {row['ROI']:>8.3f} {row['Coverage']:>9.3f}"
        )


def _calibration_view(picks: pd.DataFrame) -> None:
    if "WinProbability" not in picks.columns or picks["WinProbability"].isna().all():
        print("\n--- Calibration: no WinProbability available ---")
        return
    df = picks[picks["WinProbability"].notna()].copy()
    df["Win"] = (df["FinishingPosition"] == 1).astype(float)
    df["ProbBand"] = pd.cut(
        df["WinProbability"],
        bins=[0, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 1.0],
        labels=["<10%", "10-15%", "15-20%", "20-25%", "25-30%", "30-40%", "40%+"],
    )
    cal = df.groupby("ProbBand", observed=True).agg(
        Bets=("Win", "count"),
        ActualWinRate=("Win", "mean"),
        AvgPredicted=("WinProbability", "mean"),
    ).reset_index()
    print("\n--- Calibration (predicted vs actual win rate) ---")
    print(f"  {'Band':<10} {'Bets':>6} {'PredictedProb':>14} {'ActualWinRate':>14}")
    print("  " + "-" * 48)
    for _, row in cal.iterrows():
        print(
            f"  {str(row['ProbBand']):<10} {int(row['Bets']):>6}"
            f" {row['AvgPredicted']:>14.3f} {row['ActualWinRate']:>14.3f}"
        )


# ── Candidate rules ───────────────────────────────────────────────────────────

def _candidate_rules(picks: pd.DataFrame) -> pd.DataFrame:
    total = len(picks)
    baseline_wr = (picks["FinishingPosition"] == 1).mean()
    baseline_roi = _roi(picks)
    rows = []

    def evaluate(mask: pd.Series, name: str) -> None:
        kept = picks[~mask]
        if len(kept) / total < 0.50:
            return
        wr = (kept["FinishingPosition"] == 1).mean() if len(kept) else 0.0
        r = _roi(kept)
        rows.append({
            "Rule": name,
            "ExcludedBets": int(mask.sum()),
            "CoverageAfter": len(kept) / total,
            "WinRateAfter": wr,
            "WinRateDelta": wr - baseline_wr,
            "ROIAfter": r,
            "ROIDelta": r - baseline_roi,
        })

    if "FieldSize" in picks.columns and picks["FieldSize"].notna().any():
        for n in [9, 13, 17, 21]:
            evaluate(picks["FieldSize"] >= n, f"Exclude FieldSize >= {n}")
        for n in [3, 5, 7]:
            evaluate(picks["FieldSize"] <= n, f"Exclude FieldSize <= {n}")

    if "RaceType" in picks.columns:
        for val in picks["RaceType"].dropna().unique():
            evaluate(picks["RaceType"] == val, f"Exclude RaceType={val}")

    if "RaceClass" in picks.columns and picks["RaceClass"].notna().any():
        for val in picks["RaceClass"].dropna().unique():
            if (picks["RaceClass"] == val).sum() >= 10:
                evaluate(picks["RaceClass"] == val, f"Exclude RaceClass={val}")

    if "Going" in picks.columns and picks["Going"].notna().any():
        for val in picks["Going"].dropna().unique():
            if (picks["Going"] == val).sum() >= 10:
                evaluate(picks["Going"] == val, f"Exclude Going={val}")

    if not rows:
        return pd.DataFrame(columns=[
            "Rule", "ExcludedBets", "CoverageAfter",
            "WinRateAfter", "WinRateDelta", "ROIAfter", "ROIDelta",
        ])
    return pd.DataFrame(rows).sort_values("ROIDelta", ascending=False)


def _print_candidate_rules(rules: pd.DataFrame) -> None:
    print("\n--- Candidate Hard-Race Rules (ranked by ROI improvement) ---")
    if rules.empty:
        print("  No rules improve ROI while keeping >= 50% coverage.")
        return
    print(
        f"  {'Rule':<40} {'Excluded':>8} {'Coverage':>9}"
        f" {'WRd':>7} {'ROId':>8} {'ROIAfter':>9}"
    )
    print("  " + "-" * 88)
    for _, row in rules.head(20).iterrows():
        print(
            f"  {str(row['Rule']):<40} {int(row['ExcludedBets']):>8}"
            f" {row['CoverageAfter']:>9.3f} {row['WinRateDelta']:>+7.3f}"
            f" {row['ROIDelta']:>+8.3f} {row['ROIAfter']:>9.3f}"
        )


# ── Feature nominations ────────────────────────────────────────────────────────

def _feature_nominations(picks: pd.DataFrame, segment_stats: dict) -> list:
    baseline_roi = _roi(picks)
    noms = []
    for label, seg in segment_stats.items():
        col = seg.columns[0]
        weak = seg[seg["ROI"] < baseline_roi - 0.05].sort_values("ROI")
        for _, row in weak.iterrows():
            noms.append((
                row["ROI"],
                f"{label}={row[col]} (ROI={row['ROI']:.3f}, baseline={baseline_roi:.3f},"
                f" bets={int(row['Bets'])})",
            ))
    noms.sort(key=lambda x: x[0])
    return [msg for _, msg in noms]


# ── Main entry point ──────────────────────────────────────────────────────────

def analyse(eval_csv_path: str) -> None:
    print(f"Loading eval results: {eval_csv_path}")
    df = pd.read_csv(eval_csv_path)
    print(f"  {len(df)} rows | {df['Algorithm'].nunique()} algo(s) | {df['RaceId'].nunique()} unique races")

    picks = _identify_picks(df)
    print(f"  {len(picks)} picks identified")

    print("  Joining AgeBand / Pattern / RatingBand from Results CSVs...")
    picks = _load_results_extra(picks)

    picks["DistanceBand"] = picks["DistanceInMeters"].apply(_distance_band)
    picks["FieldSizeBand"] = picks["FieldSize"].apply(_field_size_band)

    for algo in sorted(picks["Algorithm"].unique()):
        ap = picks[picks["Algorithm"] == algo].copy()
        total = len(ap)
        wins = int((ap["FinishingPosition"] == 1).sum())
        overall_roi = _roi(ap)

        print(f"\n{'=' * 70}")
        print(f"Algorithm: {algo}")
        print(f"Total bets: {total}  Win rate: {wins/total:.3f}  ROI: {overall_roi:.3f}")
        print("=" * 70)

        segment_stats: dict = {}

        for col, title in [
            ("FieldSizeBand", "Field Size"),
            ("RaceClass", "Race Class"),
            ("RaceType", "Race Type"),
            ("DistanceBand", "Distance Band"),
            ("Going", "Going"),
        ]:
            if col in ap.columns and ap[col].notna().any():
                seg = _segment_table(ap, col)
                segment_stats[title] = seg
                _print_segment_table(seg, col, title)

        if "AgeBand" in ap.columns and ap["AgeBand"].notna().any():
            seg = _segment_table(ap, "AgeBand")
            segment_stats["Age Band"] = seg
            _print_segment_table(seg, "AgeBand", "Age Band")

        if "WinProbability" in ap.columns and ap["WinProbability"].notna().any():
            ap["ConfidenceBand"] = ap["WinProbability"].apply(_confidence_band)
            seg = _segment_table(ap, "ConfidenceBand")
            seg["_order"] = seg["ConfidenceBand"].map(
                {b: i for i, b in enumerate(_BAND_ORDER)}
            ).fillna(99)
            seg = seg.sort_values("_order").drop(columns=["_order"])
            segment_stats["Confidence Band"] = seg
            _print_segment_table(seg, "ConfidenceBand", "Confidence Band (by probability)")

        _calibration_view(ap)

        rules = _candidate_rules(ap)
        _print_candidate_rules(rules)

        noms = _feature_nominations(ap, segment_stats)
        print("\n--- Feature Nomination List ---")
        if noms:
            for i, msg in enumerate(noms, 1):
                print(f"  {i:>2}. {msg}")
        else:
            print("  No segments underperform the baseline by > 0.05 ROI.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Diagnostic analysis of enriched evaluation results."
    )
    parser.add_argument("eval_csv", help="Path to the enriched evaluation results CSV")
    args = parser.parse_args()
    analyse(args.eval_csv)
