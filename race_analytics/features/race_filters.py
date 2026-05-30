import pandas as pd

from race_analytics.features.base import RaceDataProcessor


class CalculateRacesWithKnownHorsesAndJockeys(RaceDataProcessor):
    def before_process_data(self, df: pd.DataFrame) -> None:
        df["KnownHorseAndJockey"] = False

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
