import glob
import os
from pathlib import Path

import pandas as pd

_OFF_FMT = "%m/%d/%Y %H:%M:%S"


def load_results(data_dir: str | Path, months: int | None = None) -> pd.DataFrame:
    """Load Results_*.csv files from data_dir, sorted chronologically.

    If ``months`` is given, only the most-recent ``months`` monthly files are
    loaded. Files are named Results_YYYYMM.csv (one per month), so sorting by
    name descending puts the newest first; this bounds load time/memory for a
    large history when only a recent window is needed.
    """
    pattern = os.path.join(str(data_dir), "Results_*.csv")
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No Results_*.csv files found in {data_dir}")
    if months is not None:
        files = sorted(files, reverse=True)[:months]
    dfs = []
    for f in files:
        df = pd.read_csv(f)
        df["Off"] = pd.to_datetime(df["Off"], format=_OFF_FMT)
        dfs.append(df)
    return (
        pd.concat(dfs, ignore_index=True)
        .sort_values("Off", ascending=True)
        .reset_index(drop=True)
    )


def load_race_cards(data_dir: str | Path) -> pd.DataFrame:
    """Load TodaysRaceCards.csv from data_dir."""
    path = os.path.join(str(data_dir), "TodaysRaceCards.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"TodaysRaceCards.csv not found in {data_dir}")
    df = pd.read_csv(path)
    df["Off"] = pd.to_datetime(df["Off"], format=_OFF_FMT)
    return df


def load_stats(data_dir: str | Path, filename: str) -> pd.DataFrame:
    """Load a named stats CSV (e.g. 'Horse_Stats.csv') from data_dir."""
    path = os.path.join(str(data_dir), filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"{filename} not found in {data_dir}")
    return pd.read_csv(path)
