import math
from typing import Any
import numpy as np
import pandas as pd

from race_analytics.features.base import RaceDataProcessor
from race_analytics.features.transforms import (
    surface_categories,
    going_categories,
    race_type_categories,
)


class CalculateHorsesStats(RaceDataProcessor):
    NUMBER_OF_PRIOR_RACES = "NumberOfPriorRaces"
    LAST_RACE_GOING = "LastRaceGoing"
    LAST_RACE_SURFACE = "LastRaceSurface"
    LAST_RACE_DISTANCE = "LastRaceDistanceInMeters"
    LAST_RACE_WEIGHT = "LastRaceWeightInPounds"
    LAST_RACE_SPEED = "LastRaceSpeed"
    DAYS_REST_SINCE_LAST_RACE = "DaysRested"
    LAST_RACE_ODDS = "LastRaceDecimalOdds"
    LAST_RACE_OFFICIAL_RATING = "LastRaceOfficialRating"
    LAST_RACE_RACING_POST_RATING = "LastRaceRacingPostRating"
    LAST_RACE_TOP_SPEED_RATING = "LastRaceTopSpeedRating"
    AVG_RELATIVE_FINISHING_POSITION = "LastRaceAvgRelFinishingPosition"
    LAST3_AVG_SPEED = "Last3RaceAvgSpeed"
    LAST3_SPEED_TREND = "Last3RaceSpeedTrend"
    LAST3_AVG_REL_POS = "Last3AvgRelFinishingPosition"
    ONE_DAY = np.timedelta64(1, "D")

    def before_process_data(self, df: pd.DataFrame) -> None:
        self.new_column_names = (
            [
                self.NUMBER_OF_PRIOR_RACES,
                self.LAST_RACE_GOING,
                self.LAST_RACE_SURFACE,
                self.LAST_RACE_DISTANCE,
                self.LAST_RACE_WEIGHT,
                self.LAST_RACE_SPEED,
                self.DAYS_REST_SINCE_LAST_RACE,
                self.LAST_RACE_ODDS,
                self.LAST_RACE_OFFICIAL_RATING,
                self.LAST_RACE_RACING_POST_RATING,
                self.LAST_RACE_TOP_SPEED_RATING,
                self.AVG_RELATIVE_FINISHING_POSITION,
                self.LAST3_AVG_SPEED,
                self.LAST3_SPEED_TREND,
                self.LAST3_AVG_REL_POS,
            ]
            + [f"LastRace{surface}" for surface in surface_categories]
            + [f"LastRace{going}" for going in going_categories]
            + [f"LastRace{rt}" for rt in race_type_categories]
        )
        string_cols = {self.LAST_RACE_GOING, self.LAST_RACE_SURFACE}
        for col in self.new_column_names:
            df[col] = None if col in string_cols else np.nan
        df[self.NUMBER_OF_PRIOR_RACES] = 1.0

    def update(
        self, df: pd.DataFrame, history: pd.DataFrame, daily_slice: pd.DataFrame
    ) -> None:
        slice_date = np.datetime64(daily_slice["Off"].min().date())
        slice_horses = daily_slice["HorseId"].unique().tolist()
        horse_history = history[history["HorseId"].isin(slice_horses)].sort_values(
            ["HorseId", "Off"], ascending=[True, False]
        )
        if len(horse_history) > 0:
            stats = horse_history.groupby("HorseId").apply(
                lambda g: self.__calculate_counts_for_race_group(slice_date, g),
                include_groups=False,
            )
            daily_stats = pd.merge(
                daily_slice.drop(self.new_column_names, axis=1, errors="ignore"),
                stats,
                how="left",
                on=["HorseId"],
            )
            try:
                df.loc[df.index.isin(daily_slice.index), self.new_column_names] = (
                    daily_stats[self.new_column_names].values
                )
            except Exception as e:
                print(f"Error updating stats for slice date {slice_date} with {e}")
                print("Slice horses:")
                print(slice_horses)
                print("Daily slice:")
                print(daily_slice.drop(self.new_column_names, axis=1, errors="ignore").to_string())
                print("Daily stats:")
                print(daily_stats.to_string())
                raise

    def __calculate_counts_for_race_group(
        self, current_date: np.datetime64, horse_races: pd.DataFrame
    ) -> pd.Series:
        new_columns: dict[str, Any] = {
            self.NUMBER_OF_PRIOR_RACES: horse_races["RaceId"].count()
        }
        last_race = horse_races.head(1)
        new_columns[self.LAST_RACE_GOING] = last_race["Going"].values[0]
        new_columns[self.LAST_RACE_SURFACE] = last_race["Surface"].values[0]
        new_columns[self.LAST_RACE_DISTANCE] = last_race["DistanceInMeters"].values[0]
        new_columns[self.LAST_RACE_WEIGHT] = last_race["WeightInPounds"].values[0]
        new_columns[self.LAST_RACE_SPEED] = last_race["Speed"].values[0]
        new_columns[self.DAYS_REST_SINCE_LAST_RACE] = math.ceil(
            (current_date - last_race["Off"].values[0]) / self.ONE_DAY
        )
        new_columns[self.LAST_RACE_ODDS] = last_race["DecimalOdds"].values[0]
        new_columns[self.LAST_RACE_OFFICIAL_RATING] = last_race["OfficialRating"].values[0]
        new_columns[self.LAST_RACE_RACING_POST_RATING] = last_race["RacingPostRating"].values[0]
        new_columns[self.LAST_RACE_TOP_SPEED_RATING] = last_race["TopSpeedRating"].values[0]
        new_columns[self.AVG_RELATIVE_FINISHING_POSITION] = (
            horse_races["FinishingPosition"] / horse_races["HorseCount"]
        ).mean()
        last3 = horse_races.head(3)
        last3_speeds = last3["Speed"].dropna()
        if len(last3_speeds) >= 3:
            last3_avg = last3_speeds.mean()
            new_columns[self.LAST3_AVG_SPEED] = last3_avg
            new_columns[self.LAST3_SPEED_TREND] = new_columns[self.LAST_RACE_SPEED] - last3_avg
        else:
            new_columns[self.LAST3_AVG_SPEED] = np.nan
            new_columns[self.LAST3_SPEED_TREND] = np.nan
        new_columns[self.LAST3_AVG_REL_POS] = (
            (last3["FinishingPosition"] / last3["HorseCount"]).mean()
            if len(last3) >= 3
            else np.nan
        )
        for going in going_categories:
            new_columns[f"LastRace{going}"] = last_race[going].values[0]
        for surface in surface_categories:
            new_columns[f"LastRace{surface}"] = last_race[surface].values[0]
        for rt in race_type_categories:
            new_columns[f"LastRace{rt}"] = last_race[rt].values[0]
        return pd.Series(new_columns, index=self.new_column_names)


def _extract_last3_stats(races: pd.DataFrame) -> pd.DataFrame:
    """Per-horse Last-3 aggregates over the 3 most recent races, inclusive of
    the latest. Mirrors CalculateHorsesStats but rolls the most recent race in,
    consistent with how extract_horse_stats uses the horse's actual most recent
    race for the other LastRace* columns."""
    recent = (
        races.sort_values(["HorseId", "Off"], ascending=[True, False])
        .groupby("HorseId")
        .head(3)
        .copy()
    )
    recent["_RelPos"] = recent["FinishingPosition"] / recent["HorseCount"]

    def _agg(g: pd.DataFrame) -> pd.Series:
        speeds = g["Speed"].dropna()
        if len(speeds) >= 3:
            avg_speed = speeds.mean()
            trend = g.iloc[0]["Speed"] - avg_speed
        else:
            avg_speed = np.nan
            trend = np.nan
        rel_pos = g["_RelPos"].mean() if len(g) >= 3 else np.nan
        return pd.Series(
            {
                "Last3RaceAvgSpeed": avg_speed,
                "Last3RaceSpeedTrend": trend,
                "Last3AvgRelFinishingPosition": rel_pos,
            }
        )

    return (
        recent.groupby("HorseId").apply(_agg, include_groups=False).reset_index()
    )


def extract_horse_stats(races: pd.DataFrame) -> pd.DataFrame:
    """One row per horse with stats updated through the most recent race, for use in predict()."""
    last = (
        races.sort_values(["HorseId", "Off"], ascending=[True, False])
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
    out = last[[c for c in cols if c in last.columns]].rename(columns=rename)
    return out.merge(_extract_last3_stats(races), on="HorseId", how="left")
