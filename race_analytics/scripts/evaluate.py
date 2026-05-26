import os
import argparse
import gc
import glob
import pandas as pd
import numpy as np
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from race_analytics.features.transforms import (
    encode_surfaces,
    encode_going,
    encode_race_type,
    calculate_speed,
    clean_weight,
    calculate_horse_count,
)
from race_analytics.features.race_filters import CalculateRacesWithKnownHorsesAndJockeys
from race_analytics.features.horse_stats import CalculateHorsesStats, extract_horse_stats
from race_analytics.features.jockey_stats import CalculateJockeyStats, extract_jockey_stats
from race_analytics.utils.scoring import accuracy, roi
from race_analytics.algorithms import ALGORITHMS
from race_analytics.algorithms.market_favourite import MarketFavouriteBaseline

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)), "Data")

_DEFAULT_FOLDS = 14
_DEFAULT_TRAINING_MONTHS = 7


def _extract_known_races(fold_df: pd.DataFrame) -> pd.DataFrame:
    """Return only races where every horse and jockey is known from training history."""
    return fold_df[fold_df["KnownHorseAndJockey"] == True].copy()




def _fold_dates(folds: int) -> list:
    yesterday = date.today() - timedelta(days=1)
    return [yesterday - timedelta(days=i) for i in range(folds)]


_MAX_MONTHLY_FILES = 9  # 7 months can straddle up to 8 files; 9 gives a safe margin


def _load_window(fold_date: date, training_months: int) -> pd.DataFrame:
    """Load training_months of completed races up to and including fold_date.

    Reads the _MAX_MONTHLY_FILES most-recent Results_*.csv files (sorted
    descending by name so newest are first, matching FeatureAnalysis.py),
    then date-filters to the exact window.
    """
    start = fold_date - relativedelta(months=training_months)
    recent_files = sorted(
        glob.glob(os.path.join(_DATA_DIR, "Results_*.csv")), reverse=True
    )[:_MAX_MONTHLY_FILES]
    dfs = []
    for f in recent_files:
        df = pd.read_csv(f)
        df["Off"] = pd.to_datetime(df["Off"], format="%m/%d/%Y %H:%M:%S")
        df = df[
            (df["Off"].dt.date >= start)
            & (df["Off"].dt.date <= fold_date)
            & (df["ResultStatus"] == "CompletedRace")
        ]
        if len(df) > 0:
            dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs).reset_index(drop=True)


_KEEP_COLS = [
    "RaceId",
    "CourseId",
    "CourseName",
    "RaceType",
    "Off",
    "DecimalOdds",
    "OfficialRating",
    "RacingPostRating",
    "TopSpeedRating",
    "DistanceInMeters",
    "Going",
    "Surface",
    "HorseId",
    "HorseName",
    "JockeyId",
    "JockeyName",
    "TrainerId",
    "TrainerName",
    "Age",
    "HeadGear",
    "RaceCardNumber",
    "StallNumber",
    "WeightInPounds",
    "FinishingPosition",
    "OverallBeatenDistance",
    "RaceTimeInSeconds",
    "ResultStatus",
]


def _engineer_features(races: pd.DataFrame) -> pd.DataFrame:
    """Full in-memory feature engineering pipeline (mirrors FeatureAnalysis.py)."""
    races = races[[c for c in _KEEP_COLS if c in races.columns]].copy()
    races["Wins"] = (races["FinishingPosition"] == 1).astype(int)
    races = encode_surfaces(races)
    races = encode_going(races)
    races = encode_race_type(races)
    races = calculate_speed(races)
    races = clean_weight(races)
    races = calculate_horse_count(races)
    CalculateRacesWithKnownHorsesAndJockeys().process_race_data(races)
    gc.collect()
    CalculateHorsesStats().process_race_data(races)
    gc.collect()
    CalculateJockeyStats().process_race_data(races)
    gc.collect()
    return races


def _race_card(fold_df: pd.DataFrame) -> pd.DataFrame:
    """Raw race card columns needed by predict() — it re-encodes Surface/Going/RaceType."""
    cols = [
        "RaceId",
        "HorseId",
        "JockeyId",
        "Surface",
        "Going",
        "RaceType",
        "DistanceInMeters",
        "WeightInPounds",
        "OfficialRating",
        "RacingPostRating",
        "TopSpeedRating",
    ]
    return fold_df[[c for c in cols if c in fold_df.columns]].copy()


def _results(fold_df: pd.DataFrame) -> pd.DataFrame:
    return fold_df[
        ["RaceId", "HorseId", "FinishingPosition", "DecimalOdds", "ResultStatus"]
    ].copy()


def _print_race_results(preds: pd.DataFrame, known_fold: pd.DataFrame) -> None:
    if preds.empty:
        return
    info = known_fold[
        [
            "RaceId",
            "HorseId",
            "HorseName",
            "CourseName",
            "Off",
            "FinishingPosition",
            "DecimalOdds",
        ]
    ].copy()
    merged = preds.merge(info, on=["RaceId", "HorseId"], how="left").sort_values("Off")
    for _, row in merged.iterrows():
        won = row["FinishingPosition"] == 1
        pos = (
            int(row["FinishingPosition"]) if pd.notna(row["FinishingPosition"]) else "?"
        )
        odds = f"{row['DecimalOdds']:.2f}" if pd.notna(row["DecimalOdds"]) else "N/A"
        icon = "+" if won else "-"
        time_str = row["Off"].strftime("%H:%M") if pd.notna(row["Off"]) else "?"
        horse = str(row.get("HorseName", "Unknown"))[:30]
        course = str(row.get("CourseName", "Unknown"))[:20]
        print(
            f"      {icon} {time_str}  {course:<20}  {horse:<30}  pos={pos}  odds={odds}"
        )


def _resolve_algorithms(names: list[str] | None) -> list:
    """Return algorithm instances to run, or raise SystemExit on unknown names."""
    algo_map = {type(a).__name__: a for a in ALGORITHMS}
    if not names:
        return list(ALGORITHMS)
    unknown = [n for n in names if n not in algo_map]
    if unknown:
        available = ", ".join(algo_map)
        raise SystemExit(
            f"Unknown algorithm(s): {', '.join(unknown)}\nAvailable: {available}"
        )
    return [algo_map[n] for n in names]


def evaluate(
    folds: int = _DEFAULT_FOLDS,
    training_months: int = _DEFAULT_TRAINING_MONTHS,
    algorithms: list[str] | None = None,
) -> None:
    fold_dates = _fold_dates(folds)
    selected_algos = _resolve_algorithms(algorithms)
    algo_names = [type(a).__name__ for a in selected_algos]
    all_preds = {n: [] for n in algo_names}
    all_results_store = {n: [] for n in algo_names}
    all_fav_preds = {n: [] for n in algo_names}
    baseline = MarketFavouriteBaseline()

    for fold_date in fold_dates:
        print(f"\n--- Fold: {fold_date} ---")
        raw = _load_window(fold_date, training_months)
        if raw.empty:
            print("  No data, skipping")
            continue
        print(f"  Loaded {len(raw)} rows — engineering features:")
        races = _engineer_features(raw)
        train_df = races[races["Off"].dt.date < fold_date].copy()
        fold_df = races[races["Off"].dt.date == fold_date].copy()
        known_fold = _extract_known_races(fold_df)

        if known_fold.empty:
            print("  No known races, skipping")
            continue

        horse_stats = extract_horse_stats(train_df)
        jockey_stats = extract_jockey_stats(train_df)
        card = _race_card(known_fold)
        results_df = _results(known_fold)

        for algo in selected_algos:
            name = type(algo).__name__
            print(f"  Fitting {name}...", flush=True)
            algo.fit(train_df)
            preds = algo.predict(card, horse_stats, jockey_stats)
            acc = accuracy(preds, results_df)
            r = roi(preds, results_df)
            fav_preds = baseline.predict(preds["RaceId"], results_df)
            fav_acc = accuracy(fav_preds, results_df)
            fav_r = roi(fav_preds, results_df)
            print(
                f"  {name}: accuracy={acc:.3f}, roi={r:.3f}, races={len(preds)} | favourite: accuracy={fav_acc:.3f}, roi={fav_r:.3f}, races={len(fav_preds)}"
            )
            _print_race_results(preds, known_fold)
            all_preds[name].append(preds)
            all_results_store[name].append(results_df)
            all_fav_preds[name].append(fav_preds)

        gc.collect()

    print("\n=== Summary ===")
    print(
        f"{'Algorithm':<40} {'Accuracy':>10} {'ROI':>10} {'Races':>8} {'Fav Accuracy':>14} {'Fav ROI':>10}"
    )
    print("-" * 98)
    for name in algo_names:
        if not all_preds[name]:
            print(
                f"  {name:<40} {'N/A':>10} {'N/A':>10} {'0':>8} {'N/A':>14} {'N/A':>10}"
            )
            continue
        combined_preds = pd.concat(all_preds[name]).reset_index(drop=True)
        combined_results = pd.concat(all_results_store[name]).reset_index(drop=True)
        acc = accuracy(combined_preds, combined_results)
        r = roi(combined_preds, combined_results)
        combined_fav_preds = pd.concat(all_fav_preds[name]).reset_index(drop=True)
        fav_acc = accuracy(combined_fav_preds, combined_results)
        fav_r = roi(combined_fav_preds, combined_results)
        print(
            f"  {name:<40} {acc:>10.3f} {r:>10.3f} {len(combined_preds):>8} {fav_acc:>14.3f} {fav_r:>10.3f}"
        )


if __name__ == "__main__":
    # Usage:
    #   python -m race_analytics.scripts.evaluate
    #   python -m race_analytics.scripts.evaluate --folds 14 --training-months 7
    #   python -m race_analytics.scripts.evaluate --algorithms RidgeRegressionAlgorithm
    #
    # Quick integration test (fast):
    #   python -m race_analytics.scripts.evaluate --folds 2 --training-months 2
    parser = argparse.ArgumentParser(
        description="Walk-forward evaluation of racing algorithms."
    )
    parser.add_argument(
        "--folds",
        type=int,
        default=_DEFAULT_FOLDS,
        help=f"Number of daily evaluation folds (default: {_DEFAULT_FOLDS})",
    )
    parser.add_argument(
        "--training-months",
        type=int,
        default=_DEFAULT_TRAINING_MONTHS,
        dest="training_months",
        help=f"Months of history used to train each fold (default: {_DEFAULT_TRAINING_MONTHS})",
    )
    parser.add_argument(
        "--algorithms",
        type=lambda s: [x.strip() for x in s.split(",")],
        default=None,
        help="Comma-separated list of algorithm class names to run (default: all registered algorithms)",
    )
    args = parser.parse_args()
    evaluate(
        folds=args.folds,
        training_months=args.training_months,
        algorithms=args.algorithms,
    )
