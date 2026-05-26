"""
Count races available under current KnownHorseAndJockey filter vs TSR-complete filter.
Run with: python -m race_analytics.scripts.race_count_analysis
"""
import gc
import numpy as np
import pandas as pd
from datetime import date, timedelta

from race_analytics.scripts.evaluate import _load_window, _engineer_features, _extract_known_races

FOLDS = 60
TRAINING_MONTHS = 7
MAX_HORSES = 10


def count_fold(fold_date: date) -> dict | None:
    raw = _load_window(fold_date, TRAINING_MONTHS)
    if raw.empty:
        return None
    races = _engineer_features(raw)
    fold_df = races[races["Off"].dt.date == fold_date].copy()
    known = _extract_known_races(fold_df)
    if known.empty:
        return None

    # Apply max_horses filter (same as algorithms)
    horse_counts = known.groupby("RaceId")["HorseId"].transform("count")
    known = known[horse_counts <= MAX_HORSES].copy()
    if known.empty:
        return None

    race_ids = known["RaceId"].unique()
    total_known = len(race_ids)

    # TSR-complete: every horse in the race has a TopSpeedRating
    tsr_complete = 0
    or_complete = 0
    rpr_complete = 0
    tsr_or_complete = 0  # TSR OR OfficialRating complete

    for race_id in race_ids:
        race = known[known["RaceId"] == race_id]
        has_tsr = race["TopSpeedRating"].notna().all()
        has_or = race["OfficialRating"].notna().all()
        has_rpr = race["RacingPostRating"].notna().all()
        if has_tsr:
            tsr_complete += 1
        if has_or:
            or_complete += 1
        if has_rpr:
            rpr_complete += 1
        if has_tsr or has_or:
            tsr_or_complete += 1

    return {
        "date": fold_date,
        "known": total_known,
        "tsr_complete": tsr_complete,
        "or_complete": or_complete,
        "rpr_complete": rpr_complete,
        "tsr_or_complete": tsr_or_complete,
        "tsr_pct": tsr_complete / total_known if total_known else 0,
        "or_pct": or_complete / total_known if total_known else 0,
    }


def main():
    fold_dates = [date.today() - timedelta(days=1) - timedelta(days=i) for i in range(FOLDS)]

    results = []
    for fold_date in fold_dates:
        print(f"  {fold_date}...", end=" ", flush=True)
        r = count_fold(fold_date)
        if r:
            print(f"known={r['known']}  tsr={r['tsr_complete']}  or={r['or_complete']}")
            results.append(r)
        else:
            print("no data")
        gc.collect()

    if not results:
        print("No data.")
        return

    df = pd.DataFrame(results)

    print("\n" + "=" * 65)
    print("  Race availability across 60 folds")
    print("=" * 65)
    print(f"\n  {'Filter':<40} {'Avg/day':>8}  {'Total':>7}  {'% of known':>10}")
    print(f"  {'-'*40}  {'-'*8}  {'-'*7}  {'-'*10}")

    total_known = df["known"].sum()
    avg_known = df["known"].mean()
    print(f"  {'KnownHorseAndJockey (current)':<40} {avg_known:>8.1f}  {total_known:>7}  {'100%':>10}")

    for col, label in [
        ("tsr_complete",  "+ TopSpeedRating complete"),
        ("or_complete",   "+ OfficialRating complete"),
        ("rpr_complete",  "+ RacingPostRating complete"),
        ("tsr_or_complete", "+ TSR OR OfficialRating complete"),
    ]:
        total = df[col].sum()
        avg = df[col].mean()
        pct = 100 * total / total_known if total_known else 0
        print(f"  {label:<40} {avg:>8.1f}  {total:>7}  {pct:>9.1f}%")

    print(f"\n  Days with zero TSR-complete races: {(df['tsr_complete'] == 0).sum()} / {len(df)}")
    print(f"  Days with zero OR-complete races:  {(df['or_complete'] == 0).sum()} / {len(df)}")
    print(f"\n  TSR-complete races per day distribution:")
    bins = [0, 1, 3, 5, 10, 50]
    labels = ["0", "1-2", "3-4", "5-9", "10+"]
    for i, (lo, hi, lbl) in enumerate(zip(bins, bins[1:], labels)):
        if i == 0:
            count = (df["tsr_complete"] == 0).sum()
        else:
            count = ((df["tsr_complete"] >= lo) & (df["tsr_complete"] < hi)).sum()
        bar = "#" * count
        print(f"    {lbl:>5} races/day: {count:>3} days  {bar}")


if __name__ == "__main__":
    main()
