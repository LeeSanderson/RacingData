import sys
import os
# Data/ must be on sys.path so utils.* and algorithms imports resolve
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.dirname(_SCRIPTS_DIR)
sys.path.insert(0, _DATA_DIR)

import gc
import glob
import pandas as pd
import numpy as np
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from utils.data_transforms import (
    encode_surfaces,
    encode_going,
    encode_race_type,
    calculate_speed,
    clean_weight,
    calculate_horse_count,
    surface_categories,
    going_categories,
    race_type_categories,
)
from utils.data_analysis import (
    CalculateRacesWithKnownHorsesAndJockeys,
    CalculateHorsesStats,
    CalculateJockeyStats,
)
from utils.scoring import accuracy, roi
from algorithms import ALGORITHMS


_EVAL_DAYS = 14
_TRAINING_MONTHS = 7


def _extract_known_races(fold_df: pd.DataFrame) -> pd.DataFrame:
    """Return only races where every horse and jockey is known from training history."""
    return fold_df[fold_df["KnownHorseAndJockey"] == True].copy()


def _compute_horse_stats(train_df: pd.DataFrame) -> pd.DataFrame:
    """One row per horse: stats from most recent training race, for use in predict()."""
    last = (
        train_df.sort_values(["HorseId", "Off"], ascending=[True, False])
        .groupby("HorseId")
        .first()
        .reset_index()
    )
    n = last["NumberOfPriorRaces"].fillna(0)
    last["LastRaceAvgRelFinishingPosition"] = (
        (last["LastRaceAvgRelFinishingPosition"].fillna(0) * n)
        + (last["FinishingPosition"] / last["HorseCount"])
    ) / (n + 1)

    rename = {
        "Off": "LastOff",
        "DistanceInMeters": "LastRaceDistanceInMeters",
        "WeightInPounds": "LastRaceWeightInPounds",
        "Speed": "LastRaceSpeed",
        **{s: f"LastRace{s}" for s in surface_categories},
        **{g: f"LastRace{g}" for g in going_categories},
        **{r: f"LastRace{r}" for r in race_type_categories},
    }
    cols = [
        "HorseId", "Off", "DistanceInMeters", "WeightInPounds", "Speed",
        "LastRaceAvgRelFinishingPosition",
        *surface_categories, *going_categories, *race_type_categories,
    ]
    return last[[c for c in cols if c in last.columns]].rename(columns=rename)


def _compute_jockey_stats(train_df: pd.DataFrame) -> pd.DataFrame:
    """One row per jockey: stats from most recent training race, for use in predict()."""
    last = (
        train_df[train_df["JockeyId"] > 0]
        .sort_values(["JockeyId", "Off"], ascending=[True, False])
        .groupby("JockeyId")
        .first()
        .reset_index()
    )
    prior = last["JockeyNumberOfPriorRaces"].fillna(0)
    wins = last["JockeyWinPercentage"].fillna(0) * prior + (last["FinishingPosition"] == 1).astype(float)
    top3 = last["JockeyTop3Percentage"].fillna(0) * prior + (last["FinishingPosition"] < 4).astype(float)
    avg_pos = (
        last["JockeyAvgRelFinishingPosition"].fillna(0) * prior
        + last["FinishingPosition"] / last["HorseCount"]
    ) / (prior + 1)
    last["JockeyNumberOfPriorRaces"] = prior + 1
    last["JockeyWinPercentage"] = wins / last["JockeyNumberOfPriorRaces"]
    last["JockeyTop3Percentage"] = top3 / last["JockeyNumberOfPriorRaces"]
    last["JockeyAvgRelFinishingPosition"] = avg_pos
    return last[[
        "JockeyId", "Off", "JockeyNumberOfPriorRaces",
        "JockeyWinPercentage", "JockeyTop3Percentage", "JockeyAvgRelFinishingPosition",
    ]].rename(columns={"Off": "LastOff"})


def _fold_dates() -> list:
    yesterday = date.today() - timedelta(days=1)
    return [yesterday - timedelta(days=i) for i in range(_EVAL_DAYS)]


_MAX_MONTHLY_FILES = 9  # 7 months can straddle up to 8 files; 9 gives a safe margin


def _load_window(fold_date: date) -> pd.DataFrame:
    """Load 7 months of completed races up to and including fold_date.

    Reads the _MAX_MONTHLY_FILES most-recent Results_*.csv files (sorted
    descending by name so newest are first, matching FeatureAnalysis.py),
    then date-filters to the exact 7-month window.
    """
    start = fold_date - relativedelta(months=_TRAINING_MONTHS)
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
    "RaceId", "CourseId", "RaceType", "Off", "DecimalOdds",
    "OfficialRating", "RacingPostRating", "TopSpeedRating",
    "DistanceInMeters", "Going", "Surface",
    "HorseId", "HorseName", "JockeyId", "JockeyName",
    "TrainerId", "TrainerName", "Age", "HeadGear",
    "RaceCardNumber", "StallNumber", "WeightInPounds",
    "FinishingPosition", "OverallBeatenDistance", "RaceTimeInSeconds",
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
    cols = ["RaceId", "HorseId", "JockeyId", "Surface", "Going", "RaceType",
            "DistanceInMeters", "WeightInPounds"]
    return fold_df[[c for c in cols if c in fold_df.columns]].copy()


def _results(fold_df: pd.DataFrame) -> pd.DataFrame:
    return fold_df[["RaceId", "HorseId", "FinishingPosition", "DecimalOdds", "ResultStatus"]].copy()


def evaluate() -> None:
    folds = _fold_dates()
    algo_names = [type(a).__name__ for a in ALGORITHMS]
    all_preds = {n: [] for n in algo_names}
    all_results_store = {n: [] for n in algo_names}

    for fold_date in folds:
        print(f"\n--- Fold: {fold_date} ---")
        raw = _load_window(fold_date)
        if raw.empty:
            print("  No data, skipping")
            continue

        races = _engineer_features(raw)
        train_df = races[races["Off"].dt.date < fold_date].copy()
        fold_df = races[races["Off"].dt.date == fold_date].copy()
        known_fold = _extract_known_races(fold_df)

        if known_fold.empty:
            print("  No known races, skipping")
            continue

        horse_stats = _compute_horse_stats(train_df)
        jockey_stats = _compute_jockey_stats(train_df)
        card = _race_card(known_fold)
        results_df = _results(known_fold)

        for algo in ALGORITHMS:
            name = type(algo).__name__
            algo.fit(train_df)
            preds = algo.predict(card, horse_stats, jockey_stats)
            acc = accuracy(preds, results_df)
            r = roi(preds, results_df)
            print(f"  {name}: accuracy={acc:.3f}, roi={r:.3f}, races={len(preds)}")
            all_preds[name].append(preds)
            all_results_store[name].append(results_df)

        gc.collect()

    print("\n=== Summary ===")
    print(f"{'Algorithm':<40} {'Accuracy':>10} {'ROI':>10} {'Races':>8}")
    print("-" * 72)
    for name in algo_names:
        if not all_preds[name]:
            print(f"  {name:<40} {'N/A':>10} {'N/A':>10} {'0':>8}")
            continue
        combined_preds = pd.concat(all_preds[name]).reset_index(drop=True)
        combined_results = pd.concat(all_results_store[name]).reset_index(drop=True)
        acc = accuracy(combined_preds, combined_results)
        r = roi(combined_preds, combined_results)
        print(f"  {name:<40} {acc:>10.3f} {r:>10.3f} {len(combined_preds):>8}")


if __name__ == "__main__":
    evaluate()
