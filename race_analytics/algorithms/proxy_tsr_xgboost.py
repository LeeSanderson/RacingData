from datetime import datetime

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

from race_analytics.algorithms.base import BaseAlgorithm, PREDICTORS
from race_analytics.algorithms.proxy_tsr import ProxyTSRModel
from race_analytics.features.transforms import encode_surfaces, encode_going, encode_race_type

RATING_COLS = ["OfficialRating", "RacingPostRating", "TopSpeedRating"]
PROXY_TSR_COLS = ["PeakProxyTSR", "LastProxyTSR", "Best5ProxyTSR"]


def _add_race_context(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "HorseCount" not in df.columns:
        df["HorseCount"] = df.groupby("RaceId")["HorseId"].transform("count")
    for col in RATING_COLS + PROXY_TSR_COLS:
        if col in df.columns:
            df[f"Rel{col}"] = df[col] - df.groupby("RaceId")[col].transform("mean")
    return df


class ProxyTSRXGBoostAlgorithm(BaseAlgorithm):
    """XGBoost win-probability classifier using proxy TSR features.

    Trains a ProxyTSRModel alongside the main classifier so predictions are
    available for all horses, not only those with a Racing Post TopSpeedRating.
    No TSR gating is applied — all KnownHorseAndJockey races are predicted.
    """

    def __init__(
        self,
        max_horses: int = 10,
        n_estimators: int = 200,
        learning_rate: float = 0.05,
        max_depth: int = 4,
        subsample: float = 1.0,
        colsample_bytree: float = 1.0,
        tune_proxy: bool = False,
    ):
        self._classifier = XGBClassifier(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            random_state=42,
            verbosity=0,
            eval_metric="logloss",
        )
        self._tune_proxy = tune_proxy
        self._proxy_model = ProxyTSRModel()
        self._horse_proxy_tsr: pd.DataFrame = pd.DataFrame()
        self._feature_cols: list[str] = []
        super().__init__(max_horses)

    def _create_model(self) -> XGBClassifier:
        return self._classifier

    def fit(self, train_df: pd.DataFrame) -> None:
        if self._tune_proxy:
            self._proxy_model.tune(train_df)
        self._proxy_model.fit(train_df)
        self._horse_proxy_tsr = self._proxy_model.compute_horse_proxy_tsr(train_df)

        df = train_df.merge(self._horse_proxy_tsr, on="HorseId", how="left")
        df = _add_race_context(df)

        abs_cols = [c for c in RATING_COLS + PROXY_TSR_COLS if c in df.columns]
        rel_cols = [f"Rel{c}" for c in RATING_COLS + PROXY_TSR_COLS if f"Rel{c}" in df.columns]
        feature_cols = PREDICTORS + abs_cols + rel_cols + ["HorseCount"]
        available = [c for c in feature_cols if c in df.columns]

        required = [c for c in PREDICTORS if c in df.columns] + ["Wins"]
        data = df[available + ["Wins"]].dropna(subset=required).copy()
        data.loc[data["DaysRested"] > 10, "DaysRested"] = 10
        data.loc[data["DaysSinceJockeyLastRaced"] > 10, "DaysSinceJockeyLastRaced"] = 10

        self._feature_cols = available
        self._classifier.fit(data[available], data["Wins"])

    def predict(
        self,
        races: pd.DataFrame,
        horse_stats: pd.DataFrame,
        jockey_stats: pd.DataFrame,
    ) -> pd.DataFrame:
        if not self._feature_cols:
            return pd.DataFrame(columns=["RaceId", "HorseId"])

        today = np.datetime64(datetime.today())
        one_day = np.timedelta64(1, "D")

        merged = pd.merge(races.copy(), horse_stats, how="left", on=["HorseId"])
        merged["DaysRested"] = np.ceil((today - pd.to_datetime(merged["LastOff"])) / one_day)
        merged.loc[merged["DaysRested"] > 10, "DaysRested"] = 10
        merged = merged.drop("LastOff", axis=1, errors="ignore")

        merged = pd.merge(merged, jockey_stats, how="left", on=["JockeyId"])
        merged["DaysSinceJockeyLastRaced"] = np.ceil(
            (today - pd.to_datetime(merged["LastOff"])) / one_day
        )
        merged.loc[merged["DaysSinceJockeyLastRaced"] > 10, "DaysSinceJockeyLastRaced"] = 10
        merged = merged.drop("LastOff", axis=1, errors="ignore")

        if not self._horse_proxy_tsr.empty:
            merged = pd.merge(merged, self._horse_proxy_tsr, on="HorseId", how="left")

        merged = encode_surfaces(merged)
        merged = encode_going(merged)
        merged = encode_race_type(merged)
        merged = _add_race_context(merged)

        available = [c for c in self._feature_cols if c in merged.columns]
        required = [c for c in PREDICTORS if c in available]
        predictable = merged[["RaceId", "HorseId"] + available].dropna(subset=required).copy()

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

        win_probs = self._classifier.predict_proba(predictable[available])[:, 1]
        predictable["WinProbability"] = win_probs
        predictable["PredictedRank"] = predictable.groupby("RaceId")["WinProbability"].rank(
            method="dense", ascending=False
        )

        return (
            predictable[predictable["PredictedRank"] == 1][["RaceId", "HorseId"]]
            .drop_duplicates(subset=["RaceId"])
            .reset_index(drop=True)
        )


class TunedProxyTSRXGBoostAlgorithm(ProxyTSRXGBoostAlgorithm):
    """ProxyTSRXGBoostAlgorithm with hyperparameters found via RandomizedSearchCV.

    Tuned params (40-iter search, 3-fold CV on 7-month window):
    n_estimators=500, max_depth=5, learning_rate=0.05, subsample=0.9, colsample_bytree=0.8
    """

    def __init__(self, max_horses: int = 10):
        super().__init__(
            max_horses=max_horses,
            n_estimators=500,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.8,
        )
