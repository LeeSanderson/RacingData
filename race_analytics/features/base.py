import sys
from abc import ABC
from datetime import timedelta

import pandas as pd


# Template-method base: process_race_data drives the per-day loop;
# before_process_data/update are optional no-op hooks subclasses override as needed
# (not @abstractmethod — subclasses may override only the hooks they care about).
class RaceDataProcessor(ABC):  # noqa: B024
    def before_process_data(self, df: pd.DataFrame) -> None:  # noqa: B027
        pass

    def update(  # noqa: B027
        self, df: pd.DataFrame, history: pd.DataFrame, daily_slice: pd.DataFrame
    ) -> None:
        pass

    def process_race_data(self, df: pd.DataFrame) -> None:
        df_start = df["Off"].min().date()
        slice_start = df_start + timedelta(days=1)
        df_end = df["Off"].max().date() + timedelta(days=1)

        days = (df_end - slice_start).days
        label = type(self).__name__
        day_num = 0
        _tty = sys.stdout.isatty()
        if _tty:
            print(f"    {label}: 0/{days} days", end="\r", flush=True)

        self.before_process_data(df)
        while slice_start < df_end:
            slice_end = slice_start + timedelta(days=1)
            history = df[df["Off"].dt.date < slice_start]
            daily_slice = df[
                (df["Off"].dt.date >= slice_start) & (df["Off"].dt.date < slice_end)
            ]
            if len(daily_slice) > 0:
                self.update(df, history, daily_slice)  # pyright: ignore[reportArgumentType]  # boolean-indexing yields DataFrame
            slice_start = slice_end
            day_num += 1
            if _tty:
                print(f"    {label}: {day_num}/{days} days", end="\r", flush=True)
        if _tty:
            print(f"    {label}: {days}/{days} days")
