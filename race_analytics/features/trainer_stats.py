import numpy as np
import pandas as pd

from race_analytics.features.base import RaceDataProcessor


class CalculateTrainerStats(RaceDataProcessor):
    NUMBER_OF_PRIOR_RACES = "TrainerNumberOfPriorRaces"
    WIN_PERCENTAGE = "TrainerWinPercentage"
    TOP_THREE_FINISH_PERCENTAGE = "TrainerTop3Percentage"
    AVG_RELATIVE_FINISHING_POSITION = "TrainerAvgRelFinishingPosition"

    def before_process_data(self, df: pd.DataFrame) -> None:
        self.new_column_names = [
            self.NUMBER_OF_PRIOR_RACES,
            self.WIN_PERCENTAGE,
            self.TOP_THREE_FINISH_PERCENTAGE,
            self.AVG_RELATIVE_FINISHING_POSITION,
        ]
        for col in self.new_column_names:
            df[col] = np.nan
        df[self.NUMBER_OF_PRIOR_RACES] = 1.0

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


def extract_trainer_stats(races: pd.DataFrame) -> pd.DataFrame:
    """One row per trainer with stats updated through the most recent race, for use in predict()."""
    last = (
        races[races["TrainerId"] > 0]
        .sort_values(["TrainerId", "Off"], ascending=[True, False])
        .groupby("TrainerId")
        .first()
        .reset_index()
    )
    prior = last["TrainerNumberOfPriorRaces"].fillna(0)
    wins = last["TrainerWinPercentage"].fillna(0) * prior + (
        last["FinishingPosition"] == 1
    ).astype(float)
    top3 = last["TrainerTop3Percentage"].fillna(0) * prior + (
        last["FinishingPosition"] < 4
    ).astype(float)
    avg_pos = (
        last["TrainerAvgRelFinishingPosition"].fillna(0) * prior
        + last["FinishingPosition"] / last["HorseCount"]
    ) / (prior + 1)
    last["TrainerNumberOfPriorRaces"] = prior + 1
    last["TrainerWinPercentage"] = wins / last["TrainerNumberOfPriorRaces"]
    last["TrainerTop3Percentage"] = top3 / last["TrainerNumberOfPriorRaces"]
    last["TrainerAvgRelFinishingPosition"] = avg_pos
    return last[
        [
            "TrainerId",
            "TrainerNumberOfPriorRaces",
            "TrainerWinPercentage",
            "TrainerTop3Percentage",
            "TrainerAvgRelFinishingPosition",
        ]
    ]
