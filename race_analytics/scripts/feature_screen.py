"""XGBoost feature importance screen for new Tier-1 features.

Loads a training window, engineers features once, fits XGBoostAlgorithm,
and reports feature importances. Features with importance > 0 are "selected"
(XGBoost assigns 0 to features that contributed no splits).

Usage:
    python -m race_analytics.scripts.feature_screen
    python -m race_analytics.scripts.feature_screen --training-months 7
"""
import argparse
import glob
import os
from datetime import date, timedelta

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

from race_analytics.algorithms.xgboost_algorithm import XGBoostAlgorithm
from race_analytics.scripts.evaluate import (
    _DEFAULT_TRAINING_MONTHS,
    _engineer_features,
    _MAX_MONTHLY_FILES,
)

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)), "Data")

_NEW_TIER1_FEATURES = frozenset({
    "RaceClass", "Age", "RelAge", "DrawPct", "RelDraw", "IsHandicap",
    "Pattern_Group1", "Pattern_Group2", "Pattern_Group3", "Pattern_Listed", "Pattern_None",
    "AgeBand_2yo", "AgeBand_3yo", "AgeBand_3yoPlus", "AgeBand_4yoPlus", "AgeBand_None",
    "SexRestriction_F", "SexRestriction_FM", "SexRestriction_Open",
})

_ODDS_KEYWORDS = ("odds", "price", "decimalodds", "fractionalodds", "startingprice")


def rank_features(importances: dict) -> list:
    """Return (feature, importance) pairs sorted by importance descending."""
    return sorted(importances.items(), key=lambda x: x[1], reverse=True)


def select_features(importances: dict, min_importance: float = 1e-6) -> set:
    """Return features with mean importance >= min_importance."""
    return {f for f, imp in importances.items() if imp >= min_importance}


def check_no_odds_features(features: list) -> bool:
    """Return True if no feature name contains odds-related keywords."""
    for feat in features:
        if any(kw in feat.lower() for kw in _ODDS_KEYWORDS):
            return False
    return True


def _load_training_window(training_months: int) -> pd.DataFrame:
    end = date.today() - timedelta(days=1)
    start = end - relativedelta(months=training_months)
    recent_files = sorted(
        glob.glob(os.path.join(_DATA_DIR, "Results_*.csv")), reverse=True
    )[:_MAX_MONTHLY_FILES]
    dfs = []
    for f in recent_files:
        df = pd.read_csv(f)
        df["Off"] = pd.to_datetime(df["Off"], format="%m/%d/%Y %H:%M:%S")
        df = df[
            (df["Off"].dt.date >= start)
            & (df["Off"].dt.date <= end)
            & (df["ResultStatus"] == "CompletedRace")
        ]
        if len(df) > 0:
            dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs).reset_index(drop=True)


def screen(training_months: int = _DEFAULT_TRAINING_MONTHS, min_importance: float = 1e-6) -> dict:
    """Fit XGBoost on a training window and return ranked feature importances."""
    print(f"Loading {training_months} months of training data...", flush=True)
    raw = _load_training_window(training_months)
    if raw.empty:
        return {"ranked": [], "selected": set(), "odds_clean": True}

    print(f"  {len(raw)} rows loaded. Engineering features...", flush=True)
    races = _engineer_features(raw)

    print("  Fitting XGBoost...", flush=True)
    algo = XGBoostAlgorithm(max_horses=10)
    algo.fit(races)

    model = algo._model
    fitted = algo._fitted_predictors
    if not hasattr(model, "feature_importances_") or not fitted:
        return {"ranked": [], "selected": set(), "odds_clean": True}

    importances = dict(zip(fitted, model.feature_importances_))
    ranked = rank_features(importances)
    selected = select_features(importances, min_importance)
    odds_clean = check_no_odds_features(list(importances.keys()))

    return {
        "ranked": ranked,
        "selected": selected,
        "odds_clean": odds_clean,
        "avg_importances": importances,
    }


def _print_report(result: dict) -> None:
    ranked = result["ranked"]
    selected = result["selected"]
    odds_clean = result["odds_clean"]

    print(f"\n=== Feature Importance Screen ===")
    print(f"  Odds-derived features present: {'NO (clean)' if odds_clean else 'YES (WARNING)'}")
    print(f"\n{'Feature':<40} {'Importance':>12} {'New?':>6} {'Selected?':>10}")
    print("-" * 72)
    for feat, imp in ranked:
        is_new = feat in _NEW_TIER1_FEATURES
        flag = "NEW" if is_new else ""
        sel = "YES" if feat in selected else "no"
        print(f"  {feat:<38} {imp:>12.6f} {flag:>6} {sel:>10}")

    new_selected = sorted(f for f in selected if f in _NEW_TIER1_FEATURES)
    new_dropped = sorted(f for f in _NEW_TIER1_FEATURES if f not in selected)
    print(f"\n=== New Tier-1 Feature Selection ===")
    print(f"  Selected ({len(new_selected)}): {', '.join(new_selected) or 'none'}")
    print(f"  Dropped  ({len(new_dropped)}): {', '.join(new_dropped) or 'none'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="XGBoost feature importance screen.")
    parser.add_argument("--training-months", type=int, default=_DEFAULT_TRAINING_MONTHS, dest="training_months")
    parser.add_argument("--min-importance", type=float, default=1e-6, dest="min_importance")
    args = parser.parse_args()

    result = screen(args.training_months, args.min_importance)
    _print_report(result)
