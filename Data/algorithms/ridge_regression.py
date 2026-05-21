import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import make_pipeline

from utils.data_transforms import encode_surfaces, encode_going, encode_race_type

PREDICTORS = [
    "DistanceInMeters",
    "WeightInPounds",
    "Surface_AllWeather",
    "Surface_Dirt",
    "Surface_Turf",
    "Going_Firm",
    "Going_Good",
    "Going_Good_To_Firm",
    "Going_Good_To_Soft",
    "Going_Heavy",
    "Going_Soft",
    "RaceType_Flat",
    "RaceType_Hurdle",
    "RaceType_Other",
    "RaceType_SteepleChase",
    "LastRaceDistanceInMeters",
    "LastRaceWeightInPounds",
    "LastRaceSpeed",
    "DaysRested",
    "LastRaceAvgRelFinishingPosition",
    "LastRaceSurface_AllWeather",
    "LastRaceSurface_Dirt",
    "LastRaceSurface_Turf",
    "LastRaceGoing_Good",
    "LastRaceGoing_Good_To_Soft",
    "LastRaceGoing_Soft",
    "LastRaceGoing_Good_To_Firm",
    "LastRaceGoing_Firm",
    "LastRaceGoing_Heavy",
    "LastRaceRaceType_Other",
    "LastRaceRaceType_Hurdle",
    "LastRaceRaceType_SteepleChase",
    "LastRaceRaceType_Flat",
    "JockeyNumberOfPriorRaces",
    "DaysSinceJockeyLastRaced",
    "JockeyWinPercentage",
    "JockeyTop3Percentage",
    "JockeyAvgRelFinishingPosition",
]


class RidgeRegressionAlgorithm:
    def __init__(self, max_horses: int = 10):
        self.max_horses = max_horses
        self._model = make_pipeline(
            StandardScaler(),
            PolynomialFeatures(degree=2, interaction_only=False),
            Ridge(),
        )

    def fit(self, train_df: pd.DataFrame) -> None:
        data = train_df[PREDICTORS + ["Speed"]].dropna().copy()
        self._model.fit(data[PREDICTORS], data["Speed"])

    def predict(
        self,
        races: pd.DataFrame,
        horse_stats: pd.DataFrame,
        jockey_stats: pd.DataFrame,
    ) -> pd.DataFrame:
        today = np.datetime64(datetime.today())
        one_day = np.timedelta64(1, "D")

        # Merge horse stats and compute DaysRested
        merged = pd.merge(races.copy(), horse_stats, how="left", on=["HorseId"])
        merged["DaysRested"] = np.ceil(
            (today - pd.to_datetime(merged["LastOff"])) / one_day
        )
        merged.loc[merged["DaysRested"] > 10, "DaysRested"] = 10
        merged = merged.drop("LastOff", axis=1, errors="ignore")

        # Merge jockey stats and compute DaysSinceJockeyLastRaced
        merged = pd.merge(merged, jockey_stats, how="left", on=["JockeyId"])
        merged["DaysSinceJockeyLastRaced"] = np.ceil(
            (today - pd.to_datetime(merged["LastOff"])) / one_day
        )
        merged.loc[merged["DaysSinceJockeyLastRaced"] > 10, "DaysSinceJockeyLastRaced"] = 10
        merged = merged.drop("LastOff", axis=1, errors="ignore")

        # Encode Surface, Going, RaceType from raw race card strings
        merged = encode_surfaces(merged)
        merged = encode_going(merged)
        merged = encode_race_type(merged)

        # Keep only rows where all predictors are present
        predictable = merged[["RaceId", "HorseId"] + PREDICTORS].dropna().copy()
        if len(predictable) == 0:
            return pd.DataFrame(columns=["RaceId", "HorseId"])

        # Count original and predictable runners per race
        original_counts = (
            races.groupby("RaceId")["HorseId"]
            .agg(["count"])
            .rename(columns={"count": "OriginalCount"})
        )
        pred_counts = (
            predictable.groupby("RaceId")["HorseId"]
            .agg(["count"])
            .rename(columns={"count": "PredictableCount"})
        )
        predictable = pd.merge(predictable, original_counts, how="left", on="RaceId")
        predictable = pd.merge(predictable, pred_counts, how="left", on="RaceId")

        # Apply max_horses filter: all runners must have data and race must not exceed limit
        predictable = predictable[
            (predictable["OriginalCount"] == predictable["PredictableCount"])
            & (predictable["OriginalCount"] <= self.max_horses)
        ].copy()

        if len(predictable) == 0:
            return pd.DataFrame(columns=["RaceId", "HorseId"])

        predictable["PredictedSpeed"] = self._model.predict(predictable[PREDICTORS])
        predictable["PredictedRank"] = predictable.groupby("RaceId")[
            "PredictedSpeed"
        ].rank(method="dense", ascending=False)

        return (
            predictable[predictable["PredictedRank"] == 1][["RaceId", "HorseId"]]
            .drop_duplicates(subset=["RaceId"])
            .reset_index(drop=True)
        )
