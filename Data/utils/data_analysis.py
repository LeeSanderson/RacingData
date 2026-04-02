import math
from typing import Any
import pandas as pd
import numpy as np
from ipywidgets import IntProgress
from IPython.display import display
from datetime import timedelta
from abc import ABC

from utils.data_transforms import (
    surface_categories,
    going_categories,
    race_type_categories,
)


def calculateHorsesPerRace(races: pd.DataFrame) -> pd.DataFrame:
    groups = (
        races.groupby(["RaceId"])["HorseId"]
        .agg(["count"])
        .rename(columns={"count": "HorseCount"})
    )
    return pd.merge(races, groups, how="left", on=["RaceId"])


class RaceDataProcessor(ABC):

    def before_process_data(self, df: pd.DataFrame) -> None:
        # Update the underlying DataFrame before processing to e.g. set default values for new features
        pass

    def update(
        self, df: pd.DataFrame, history: pd.DataFrame, daily_slice: pd.DataFrame
    ) -> None:
        # Update the processor with data
        pass

    def process_race_data(self, df: pd.DataFrame) -> None:
        df_start = df["Off"].min().date()
        slice_start = df_start + timedelta(days=1)
        df_end = df["Off"].max().date() + timedelta(days=1)

        days = (df_end - slice_start).days
        f = IntProgress(min=0, max=days)  # instantiate the bar
        display(f)

        self.before_process_data(df)
        while slice_start < df_end:
            slice_end = slice_start + timedelta(days=1)
            history = df[df["Off"].dt.date < slice_start]
            daily_slice = df[
                (df["Off"].dt.date >= slice_start) & (df["Off"].dt.date < slice_end)
            ]
            if len(daily_slice) > 0:
                self.update(df, history, daily_slice)
            slice_start = slice_end
            f.value += 1


# ================================================================
# Calculate, for each race, whether the horse and jockey are known
# (i.e. have previously been involved in a race)
# ================================================================
class CalculateRacesWithKnownHorsesAndJockeys(RaceDataProcessor):
    def before_process_data(self, df: pd.DataFrame) -> None:
        df["KnownHorseAndJockey"] = False
        # df["KnownJockeyCount"] = 0
        # df["KnownHorseCount"] = 0

    def update(
        self, df: pd.DataFrame, history: pd.DataFrame, daily_slice: pd.DataFrame
    ) -> None:
        known_jockeys = history["JockeyId"].unique().tolist()
        known_runners = history["HorseId"].unique().tolist()
        temp = daily_slice.groupby("RaceId").apply(
            lambda g: self.__calculate_counts_for_race_group(
                g, known_jockeys, known_runners
            ),
            include_groups=False,
        )
        temp = temp[
            (temp["HorseCount"] == temp["KnownJockeyCount"])
            & (temp["HorseCount"] == temp["KnownHorseCount"])
        ]
        races_with_known_horses_and_jockeys = (
            temp.reset_index()["RaceId"].unique().tolist()
        )
        df.loc[
            df["RaceId"].isin(races_with_known_horses_and_jockeys),
            "KnownHorseAndJockey",
        ] = True

    def __calculate_counts_for_race_group(
        self, race_group, known_jockeys, known_runners
    ) -> pd.Series:
        new_columns = {"HorseCount": race_group["HorseId"].count()}
        new_columns["KnownHorseCount"] = race_group[
            race_group["HorseId"].isin(known_runners)
        ]["HorseId"].count()
        new_columns["KnownJockeyCount"] = race_group[
            race_group["JockeyId"].isin(known_jockeys)
        ]["JockeyId"].count()
        return pd.Series(
            new_columns, index=["HorseCount", "KnownHorseCount", "KnownJockeyCount"]
        )


# ================================================================
# Calculate, for each horse, stats based on their previous races
# ================================================================
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
            + [
                f"LastRace{race_type_category}"
                for race_type_category in race_type_categories
            ]
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
                print(
                    daily_slice.drop(
                        self.new_column_names, axis=1, errors="ignore"
                    ).to_string()
                )
                print("Daily stats:")
                print(daily_stats.to_string())
                raise

    def __calculate_counts_for_race_group(
        self, current_date: np.datetime64, horse_races: pd.DataFrame
    ) -> pd.Series:
        new_columns: dict[str, Any] = {
            self.NUMBER_OF_PRIOR_RACES: horse_races["RaceId"].count()
        }
        last_race = horse_races.head(1)  # Data already ordered in Off descending order
        new_columns[self.LAST_RACE_GOING] = last_race["Going"].values[0]
        new_columns[self.LAST_RACE_SURFACE] = last_race["Surface"].values[0]
        new_columns[self.LAST_RACE_DISTANCE] = last_race["DistanceInMeters"].values[0]
        new_columns[self.LAST_RACE_WEIGHT] = last_race["WeightInPounds"].values[0]
        new_columns[self.LAST_RACE_SPEED] = last_race["Speed"].values[0]
        new_columns[self.DAYS_REST_SINCE_LAST_RACE] = math.ceil(
            (current_date - last_race["Off"].values[0]) / self.ONE_DAY
        )
        new_columns[self.LAST_RACE_ODDS] = last_race["DecimalOdds"].values[0]
        new_columns[self.LAST_RACE_OFFICIAL_RATING] = last_race[
            "OfficialRating"
        ].values[0]
        new_columns[self.LAST_RACE_RACING_POST_RATING] = last_race[
            "RacingPostRating"
        ].values[0]
        new_columns[self.LAST_RACE_TOP_SPEED_RATING] = last_race[
            "TopSpeedRating"
        ].values[0]
        new_columns[self.AVG_RELATIVE_FINISHING_POSITION] = (
            horse_races["FinishingPosition"] / horse_races["HorseCount"]
        ).mean()
        last3 = horse_races.head(3)
        last3_speeds = last3["Speed"].dropna()
        if len(last3_speeds) >= 3:
            last3_avg = last3_speeds.mean()
            new_columns[self.LAST3_AVG_SPEED] = last3_avg
            new_columns[self.LAST3_SPEED_TREND] = (
                new_columns[self.LAST_RACE_SPEED] - last3_avg
            )
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
        for race_type_category in race_type_categories:
            new_columns[f"LastRace{race_type_category}"] = last_race[
                race_type_category
            ].values[0]
        return pd.Series(new_columns, index=self.new_column_names)


# ================================================================
# Calculate, for each jockey, stats based on their previous races
# ================================================================
class CalculateJockeyStats(RaceDataProcessor):
    NUMBER_OF_PRIOR_RACES = "JockeyNumberOfPriorRaces"
    DAYS_SINCE_LAST_RACE = "DaysSinceJockeyLastRaced"
    WIN_PERCENTAGE = "JockeyWinPercentage"
    TOP_THREE_FINISH_PERCENTAGE = "JockeyTop3Percentage"
    AVG_RELATIVE_FINISHING_POSITION = "JockeyAvgRelFinishingPosition"
    ONE_DAY = np.timedelta64(1, "D")

    def before_process_data(self, df: pd.DataFrame) -> None:
        df.loc[:, self.NUMBER_OF_PRIOR_RACES] = 1.0
        self.new_column_names = [
            self.NUMBER_OF_PRIOR_RACES,
            self.DAYS_SINCE_LAST_RACE,
            self.WIN_PERCENTAGE,
            self.TOP_THREE_FINISH_PERCENTAGE,
            self.AVG_RELATIVE_FINISHING_POSITION,
        ]

    def update(
        self, df: pd.DataFrame, history: pd.DataFrame, daily_slice: pd.DataFrame
    ) -> None:
        slice_jockeys = daily_slice["JockeyId"].unique().tolist()
        jockey_history = history[history["JockeyId"].isin(slice_jockeys)].sort_values(
            ["JockeyId", "Off"], ascending=[True, False]
        )
        if len(jockey_history) > 0:
            slice_date = np.datetime64(daily_slice["Off"].min().date())
            stats = jockey_history.groupby("JockeyId").apply(
                lambda g: self.__calculate_stats_for_jockey(slice_date, g),
                include_groups=False,
            )
            daily_stats = pd.merge(
                daily_slice.drop(self.new_column_names, axis=1, errors="ignore"),
                stats,
                how="left",
                on=["JockeyId"],
            )
            df.loc[df.index.isin(daily_slice.index), self.new_column_names] = (
                daily_stats[self.new_column_names].values
            )

    def __calculate_stats_for_jockey(
        self, current_date: np.datetime64, jockey_races: pd.DataFrame
    ) -> pd.Series:
        number_of_races = jockey_races["RaceId"].count()
        last_race = jockey_races.head(1)  # Data already ordered in Off descending order
        wins = len(jockey_races[jockey_races["FinishingPosition"] == 1])
        top_finishes = len(jockey_races[jockey_races["FinishingPosition"] < 4])
        average_position = (
            jockey_races["FinishingPosition"] / jockey_races["HorseCount"]
        ).mean()
        new_columns = {
            self.NUMBER_OF_PRIOR_RACES: number_of_races,
            self.DAYS_SINCE_LAST_RACE: math.ceil(
                (current_date - last_race["Off"].values[0]) / self.ONE_DAY
            ),
            self.WIN_PERCENTAGE: wins / number_of_races,
            self.TOP_THREE_FINISH_PERCENTAGE: top_finishes / number_of_races,
            self.AVG_RELATIVE_FINISHING_POSITION: average_position,
        }
        return pd.Series(new_columns, index=self.new_column_names)


# ================================================================
# Calculate, for each trainer, stats based on their previous races
# ================================================================
class CalculateTrainerStats(RaceDataProcessor):
    NUMBER_OF_PRIOR_RACES = "TrainerNumberOfPriorRaces"
    WIN_PERCENTAGE = "TrainerWinPercentage"
    TOP_THREE_FINISH_PERCENTAGE = "TrainerTop3Percentage"
    AVG_RELATIVE_FINISHING_POSITION = "TrainerAvgRelFinishingPosition"

    def before_process_data(self, df: pd.DataFrame) -> None:
        df.loc[:, self.NUMBER_OF_PRIOR_RACES] = 1.0
        self.new_column_names = [
            self.NUMBER_OF_PRIOR_RACES,
            self.WIN_PERCENTAGE,
            self.TOP_THREE_FINISH_PERCENTAGE,
            self.AVG_RELATIVE_FINISHING_POSITION,
        ]

    def update(
        self, df: pd.DataFrame, history: pd.DataFrame, daily_slice: pd.DataFrame
    ) -> None:
        slice_trainers = daily_slice["TrainerId"].unique().tolist()
        trainer_history = history[
            history["TrainerId"].isin(slice_trainers)
        ].sort_values(["TrainerId", "Off"], ascending=[True, False])
        if len(trainer_history) > 0:
            stats = trainer_history.groupby("TrainerId").apply(
                lambda g: self.__calculate_stats_for_trainer(g),
                include_groups=False,
            )
            daily_stats = pd.merge(
                daily_slice.drop(self.new_column_names, axis=1, errors="ignore"),
                stats,
                how="left",
                on=["TrainerId"],
            )
            df.loc[df.index.isin(daily_slice.index), self.new_column_names] = (
                daily_stats[self.new_column_names].values
            )

    def __calculate_stats_for_trainer(self, trainer_races: pd.DataFrame) -> pd.Series:
        number_of_races = trainer_races["RaceId"].count()
        wins = len(trainer_races[trainer_races["FinishingPosition"] == 1])
        top_finishes = len(trainer_races[trainer_races["FinishingPosition"] < 4])
        average_position = (
            trainer_races["FinishingPosition"] / trainer_races["HorseCount"]
        ).mean()
        new_columns = {
            self.NUMBER_OF_PRIOR_RACES: number_of_races,
            self.WIN_PERCENTAGE: wins / number_of_races,
            self.TOP_THREE_FINISH_PERCENTAGE: top_finishes / number_of_races,
            self.AVG_RELATIVE_FINISHING_POSITION: average_position,
        }
        return pd.Series(new_columns, index=self.new_column_names)
