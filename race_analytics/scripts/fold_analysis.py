"""
Analyse what distinguishes high-accuracy from low-accuracy folds for RatingsXGBoostAlgorithm.
Run with: python -m race_analytics.scripts.fold_analysis
"""
import gc
import pandas as pd
import numpy as np
from datetime import date, timedelta

from race_analytics.scripts.evaluate import (
    _load_window, _engineer_features, _extract_known_races,
    _compute_horse_stats, _compute_jockey_stats, _race_card, _results,
)
from race_analytics.algorithms.ratings_xgboost import RatingsXGBoostAlgorithm, _add_race_context
from race_analytics.utils.scoring import accuracy, roi

HIGH_ACCURACY_DATES = [
    date(2026, 4, 28),  # 0.875 accuracy, 16 races
    date(2026, 4, 16),  # 0.700 accuracy, 10 races
    date(2026, 5, 8),   # 0.692 accuracy, 13 races
    date(2026, 5, 9),   # 0.667 accuracy, 21 races
    date(2026, 4, 26),  # 0.600 accuracy, 10 races
    date(2026, 4, 17),  # 0.550 accuracy, 20 races
    date(2026, 4, 11),  # 0.524 accuracy, 21 races
]

LOW_ACCURACY_DATES = [
    date(2026, 5, 4),   # 0.185 accuracy, 27 races
    date(2026, 5, 11),  # 0.000 accuracy,  8 races
    date(2026, 4, 22),  # 0.176 accuracy, 17 races
    date(2026, 4, 21),  # 0.214 accuracy, 14 races
    date(2026, 5, 15),  # 0.077 accuracy, 13 races
    date(2026, 3, 28),  # 0.083 accuracy, 12 races
    date(2026, 4, 8),   # 0.154 accuracy, 13 races
]


def analyse_fold(fold_date: date, algo: RatingsXGBoostAlgorithm) -> dict:
    raw = _load_window(fold_date, training_months=7)
    if raw.empty:
        return {}
    races = _engineer_features(raw)
    train_df = races[races["Off"].dt.date < fold_date].copy()
    fold_df = races[races["Off"].dt.date == fold_date].copy()
    known_fold = _extract_known_races(fold_df)
    if known_fold.empty:
        return {}

    horse_stats = _compute_horse_stats(train_df)
    jockey_stats = _compute_jockey_stats(train_df)
    card = _race_card(known_fold)
    results_df = _results(known_fold)

    algo.fit(train_df)
    preds = algo.predict(card, horse_stats, jockey_stats)
    if preds.empty:
        return {}

    acc = accuracy(preds, results_df)
    r = roi(preds, results_df)

    # Merge predictions with known_fold for per-race detail
    detail = preds.merge(
        known_fold[["RaceId", "HorseId", "FinishingPosition", "DecimalOdds",
                    "HorseCount", "RaceType", "OfficialRating", "RacingPostRating",
                    "TopSpeedRating", "DistanceInMeters"]],
        on=["RaceId", "HorseId"], how="left"
    )
    detail["Won"] = (detail["FinishingPosition"] == 1).astype(int)

    # Ratings coverage in predicted races
    ratings_coverage = {
        "OfficialRating": detail["OfficialRating"].notna().mean(),
        "RacingPostRating": detail["RacingPostRating"].notna().mean(),
        "TopSpeedRating": detail["TopSpeedRating"].notna().mean(),
    }

    return {
        "date": fold_date,
        "accuracy": acc,
        "roi": r,
        "n_races": len(preds),
        "avg_field_size": detail["HorseCount"].mean(),
        "max_field_size": detail["HorseCount"].max(),
        "min_field_size": detail["HorseCount"].min(),
        "pct_small_field": (detail["HorseCount"] <= 5).mean(),
        "race_types": detail["RaceType"].value_counts().to_dict(),
        "avg_winner_odds": detail[detail["Won"] == 1]["DecimalOdds"].mean(),
        "avg_all_odds": detail["DecimalOdds"].mean(),
        "ratings_coverage": ratings_coverage,
        "avg_official_rating": detail["OfficialRating"].mean(),
    }


def print_fold_stats(label: str, stats_list: list) -> None:
    valid = [s for s in stats_list if s]
    if not valid:
        return
    print(f"\n{'='*60}")
    print(f"  {label}  ({len(valid)} folds)")
    print(f"{'='*60}")
    for s in valid:
        print(f"\n  {s['date']}  acc={s['accuracy']:.3f}  roi={s['roi']:+.2f}  races={s['n_races']}")
        print(f"    Field size: avg={s['avg_field_size']:.1f}  min={s['min_field_size']}  max={s['max_field_size']}  pct<=5={s['pct_small_field']:.0%}")
        print(f"    Winner avg odds={s['avg_winner_odds']:.2f}  all-pick avg odds={s['avg_all_odds']:.2f}")
        types = ", ".join(f"{k}:{v}" for k, v in sorted(s["race_types"].items()))
        print(f"    Race types: {types}")
        cov = s["ratings_coverage"]
        print(f"    Ratings coverage: OR={cov['OfficialRating']:.0%}  RPR={cov['RacingPostRating']:.0%}  TSR={cov['TopSpeedRating']:.0%}")

    print(f"\n  --- Averages across {label} ---")
    print(f"    Accuracy:       {np.mean([s['accuracy'] for s in valid]):.3f}")
    print(f"    ROI:            {np.mean([s['roi'] for s in valid]):+.2f}")
    print(f"    Avg field size: {np.mean([s['avg_field_size'] for s in valid]):.1f}")
    print(f"    Pct small field:{np.mean([s['pct_small_field'] for s in valid]):.0%}")
    print(f"    Winner odds:    {np.nanmean([s['avg_winner_odds'] for s in valid]):.2f}")
    rpr = np.mean([s['ratings_coverage']['RacingPostRating'] for s in valid])
    print(f"    RPR coverage:   {rpr:.0%}")


def main():
    algo = RatingsXGBoostAlgorithm(max_horses=10)

    print("Analysing HIGH-accuracy folds...")
    high_stats = []
    for d in HIGH_ACCURACY_DATES:
        print(f"  Loading {d}...", end=" ", flush=True)
        s = analyse_fold(d, algo)
        high_stats.append(s)
        if s:
            print(f"acc={s['accuracy']:.3f}  field_avg={s['avg_field_size']:.1f}")
        else:
            print("no data")
        gc.collect()

    print("\nAnalysing LOW-accuracy folds...")
    low_stats = []
    for d in LOW_ACCURACY_DATES:
        print(f"  Loading {d}...", end=" ", flush=True)
        s = analyse_fold(d, algo)
        low_stats.append(s)
        if s:
            print(f"acc={s['accuracy']:.3f}  field_avg={s['avg_field_size']:.1f}")
        else:
            print("no data")
        gc.collect()

    print_fold_stats("HIGH-accuracy folds", high_stats)
    print_fold_stats("LOW-accuracy folds", low_stats)


if __name__ == "__main__":
    main()
