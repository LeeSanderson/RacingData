from abc import abstractmethod
from datetime import datetime

import numpy as np
import pandas as pd

from race_analytics.algorithms.base import BaseAlgorithm, PREDICTORS, REQUIRED_PREDICTORS, _Estimator
from race_analytics.features.transforms import encode_surfaces, encode_going, encode_race_type


class RegressorAlgorithm(BaseAlgorithm):
    def __init__(self, max_horses: int = 10):
        super().__init__(max_horses)
        self._model: _Estimator = self._create_model()
        self._fitted_predictors: list[str] = list(PREDICTORS)

    @abstractmethod
    def _create_model(self) -> _Estimator:
        ...

    def fit(self, train_df: pd.DataFrame) -> None:
        required = [c for c in REQUIRED_PREDICTORS if c in train_df.columns]
        tolerated = [c for c in self.nan_tolerant_predictors if c in train_df.columns]
        self._fitted_predictors = required + tolerated
        data = train_df[self._fitted_predictors + ["Speed"]].dropna(subset=required + ["Speed"]).copy()
        if "DaysRested" in data.columns:
            data.loc[data["DaysRested"] > 10, "DaysRested"] = 10
        if "DaysSinceJockeyLastRaced" in data.columns:
            data.loc[data["DaysSinceJockeyLastRaced"] > 10, "DaysSinceJockeyLastRaced"] = 10
        self._model.fit(data[self._fitted_predictors], data["Speed"])

    def predict(
        self,
        races: pd.DataFrame,
        horse_stats: pd.DataFrame,
        jockey_stats: pd.DataFrame,
        trainer_stats: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        today = np.datetime64(datetime.today())
        one_day = np.timedelta64(1, "D")

        merged = pd.merge(races.copy(), horse_stats, how="left", on=["HorseId"])
        merged["DaysRested"] = np.ceil(
            (today - pd.to_datetime(merged["LastOff"])) / one_day
        )
        merged.loc[merged["DaysRested"] > 10, "DaysRested"] = 10
        merged = merged.drop("LastOff", axis=1, errors="ignore")

        merged = pd.merge(merged, jockey_stats, how="left", on=["JockeyId"])
        merged["DaysSinceJockeyLastRaced"] = np.ceil(
            (today - pd.to_datetime(merged["LastOff"])) / one_day
        )
        merged.loc[merged["DaysSinceJockeyLastRaced"] > 10, "DaysSinceJockeyLastRaced"] = 10
        merged = merged.drop("LastOff", axis=1, errors="ignore")

        if trainer_stats is not None:
            merged = pd.merge(merged, trainer_stats, how="left", on=["TrainerId"])

        merged = encode_surfaces(merged)
        merged = encode_going(merged)
        merged = encode_race_type(merged)

        required_fitted = [c for c in REQUIRED_PREDICTORS if c in self._fitted_predictors]
        predictable = merged[["RaceId", "HorseId"] + self._fitted_predictors].dropna(subset=required_fitted).copy()
        if len(predictable) == 0:
            return pd.DataFrame(columns=["RaceId", "HorseId"])

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

        predictable = predictable[
            (predictable["OriginalCount"] == predictable["PredictableCount"])
            & (predictable["OriginalCount"] <= self.max_horses)
        ].copy()

        if len(predictable) == 0:
            return pd.DataFrame(columns=["RaceId", "HorseId"])

        predictable["PredictedSpeed"] = self._model.predict(predictable[self._fitted_predictors])
        predictable["PredictedRank"] = predictable.groupby("RaceId")[
            "PredictedSpeed"
        ].rank(method="dense", ascending=False)

        return (
            predictable[predictable["PredictedRank"] == 1][["RaceId", "HorseId"]]
            .drop_duplicates(subset=["RaceId"])
            .reset_index(drop=True)
        )
