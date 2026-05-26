import pandas as pd
from datetime import timedelta
from abc import ABC


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
        label = type(self).__name__
        day_num = 0
        print(f"    {label}: 0/{days} days", end="\r", flush=True)

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
            day_num += 1
            print(f"    {label}: {day_num}/{days} days", end="\r", flush=True)
        print(f"    {label}: {days}/{days} days")


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
