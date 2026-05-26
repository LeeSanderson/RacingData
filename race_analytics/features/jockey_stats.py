import math
import numpy as np
import pandas as pd

from race_analytics.features.base import RaceDataProcessor


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
        last_race = jockey_races.head(1)
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


def extract_jockey_stats(races: pd.DataFrame) -> pd.DataFrame:
    """One row per jockey with stats updated through the most recent race, for use in predict()."""
    last = (
        races[races["JockeyId"] > 0]
        .sort_values(["JockeyId", "Off"], ascending=[True, False])
        .groupby("JockeyId")
        .first()
        .reset_index()
    )
    prior = last["JockeyNumberOfPriorRaces"].fillna(0)
    wins = last["JockeyWinPercentage"].fillna(0) * prior + (
        last["FinishingPosition"] == 1
    ).astype(float)
    top3 = last["JockeyTop3Percentage"].fillna(0) * prior + (
        last["FinishingPosition"] < 4
    ).astype(float)
    avg_pos = (
        last["JockeyAvgRelFinishingPosition"].fillna(0) * prior
        + last["FinishingPosition"] / last["HorseCount"]
    ) / (prior + 1)
    last["JockeyNumberOfPriorRaces"] = prior + 1
    last["JockeyWinPercentage"] = wins / last["JockeyNumberOfPriorRaces"]
    last["JockeyTop3Percentage"] = top3 / last["JockeyNumberOfPriorRaces"]
    last["JockeyAvgRelFinishingPosition"] = avg_pos
    return last[
        [
            "JockeyId", "Off",
            "JockeyNumberOfPriorRaces",
            "JockeyWinPercentage",
            "JockeyTop3Percentage",
            "JockeyAvgRelFinishingPosition",
        ]
    ].rename(columns={"Off": "LastOff"})
