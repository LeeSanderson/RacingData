"""
Analysis script: feature importance, baseline correlation, and ratings impact.
Run with: python -m race_analytics.scripts.analysis
"""
import gc
import glob
import os
import numpy as np
import pandas as pd
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from xgboost import XGBRegressor

from race_analytics.scripts.evaluate import (
    _load_window, _engineer_features, _compute_horse_stats,
    _compute_jockey_stats, _race_card, _extract_known_races,
)
from race_analytics.algorithms.base import PREDICTORS

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)), "Data")

RATINGS = ["OfficialRating", "RacingPostRating", "TopSpeedRating"]
EXTRA_FEATURES = ["HorseCount", "Age", "NumberOfPriorRaces", "StallNumber"]


def _load_one_fold(fold_date: date, training_months: int = 7):
    raw = _load_window(fold_date, training_months)
    if raw.empty:
        return None, None, None
    races = _engineer_features(raw)
    train_df = races[races["Off"].dt.date < fold_date].copy()
    fold_df = races[races["Off"].dt.date == fold_date].copy()
    known_fold = _extract_known_races(fold_df)
    return train_df, fold_df, known_fold


def feature_importance(train_df: pd.DataFrame) -> None:
    """Print XGBoost feature importances on the current PREDICTORS list."""
    data = train_df[PREDICTORS + ["Speed"]].dropna().copy()
    data.loc[data["DaysRested"] > 10, "DaysRested"] = 10
    data.loc[data["DaysSinceJockeyLastRaced"] > 10, "DaysSinceJockeyLastRaced"] = 10
    model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=4,
                         random_state=42, verbosity=0)
    model.fit(data[PREDICTORS], data["Speed"])
    importances = sorted(zip(PREDICTORS, model.feature_importances_),
                         key=lambda x: x[1], reverse=True)
    print("\n--- XGBoost Feature Importances (current PREDICTORS) ---")
    for name, imp in importances:
        bar = "#" * int(imp * 400)
        print(f"  {name:<45} {imp:.4f}  {bar}")


def ratings_availability(train_df: pd.DataFrame) -> None:
    """Check how many training rows have ratings populated."""
    print("\n--- Ratings availability in training data ---")
    for col in RATINGS + EXTRA_FEATURES:
        if col in train_df.columns:
            n_valid = train_df[col].notna().sum()
            pct = 100 * n_valid / len(train_df)
            print(f"  {col:<30} {n_valid:>8} / {len(train_df):>8} rows  ({pct:.1f}%)")
        else:
            print(f"  {col:<30} NOT IN DATAFRAME")


def correlation_with_winning(train_df: pd.DataFrame) -> None:
    """Point-biserial correlation of numeric features with Wins (horse won its race)."""
    print("\n--- Feature correlation with Wins (1=won, 0=lost) ---")
    candidates = PREDICTORS + RATINGS + EXTRA_FEATURES + ["LastRaceSpeed"]
    rows = []
    for col in candidates:
        if col not in train_df.columns:
            continue
        sub = train_df[[col, "Wins"]].dropna()
        if len(sub) < 100 or sub[col].std() == 0:
            continue
        corr = sub[col].corr(sub["Wins"])
        rows.append((col, corr, len(sub)))
    rows.sort(key=lambda x: abs(x[1]), reverse=True)
    for col, corr, n in rows:
        bar = "#" * int(abs(corr) * 200)
        sign = "+" if corr > 0 else "-"
        print(f"  {col:<45} {sign}{abs(corr):.4f}  {bar}  (n={n})")


def ratings_speed_correlation(train_df: pd.DataFrame) -> None:
    """Correlation of ratings with Speed (the regression target)."""
    print("\n--- Ratings correlation with Speed (regression target) ---")
    for col in RATINGS:
        if col not in train_df.columns:
            continue
        sub = train_df[[col, "Speed"]].dropna()
        corr = sub[col].corr(sub["Speed"])
        print(f"  {col:<30} corr with Speed = {corr:.4f}  (n={len(sub)})")


def relative_rating_potential(train_df: pd.DataFrame) -> None:
    """Check if a horse's rating *relative to its field* predicts wins."""
    print("\n--- Relative rating (horse vs field avg) correlation with Wins ---")
    for col in RATINGS:
        if col not in train_df.columns:
            continue
        sub = train_df[["RaceId", col, "Wins"]].dropna().copy()
        field_avg = sub.groupby("RaceId")[col].transform("mean")
        sub["RelRating"] = sub[col] - field_avg
        corr = sub["RelRating"].corr(sub["Wins"])
        print(f"  Relative {col:<22} corr with Wins = {corr:.4f}  (n={len(sub)})")


def main():
    fold_date = date.today() - timedelta(days=1)
    print(f"Loading fold: {fold_date} (7 months training)...")
    train_df, fold_df, known_fold = _load_one_fold(fold_date)
    if train_df is None:
        print("No data available.")
        return

    print(f"Training rows: {len(train_df)}, fold rows: {len(fold_df) if fold_df is not None else 0}")

    feature_importance(train_df)
    ratings_availability(train_df)
    correlation_with_winning(train_df)
    ratings_speed_correlation(train_df)
    relative_rating_potential(train_df)


if __name__ == "__main__":
    main()
