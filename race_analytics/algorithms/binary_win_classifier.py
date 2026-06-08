from datetime import datetime
from typing import ClassVar

import numpy as np
import pandas as pd

from race_analytics.algorithms.base import (
    FieldPredictorBaseAlgorithm,
    REQUIRED_PREDICTORS,
    OPTIONAL_PREDICTORS,
)
from race_analytics.features.transforms import (
    encode_surfaces,
    encode_going,
    encode_race_type,
    calculate_weight_change,
    calculate_distance_change,
    calculate_surface_switch,
    calculate_code_switch,
    calculate_race_class,
    calculate_age_features,
    calculate_draw_features,
    encode_pattern,
    calculate_is_handicap,
    encode_age_band,
    encode_sex_restriction,
    encode_headgear,
)


def _add_race_context(df: pd.DataFrame, extra_cols: list[str]) -> pd.DataFrame:
    df = df.copy()
    if "HorseCount" not in df.columns:
        df["HorseCount"] = df.groupby("RaceId")["HorseId"].transform("count")
    for col in extra_cols:
        if col in df.columns:
            df[f"Rel{col}"] = df[col] - df.groupby("RaceId")[col].transform("mean")
    return df


class BinaryWinClassifierAlgorithm(FieldPredictorBaseAlgorithm):
    extra_nan_tolerant_features: ClassVar[list[str]] = []

    def __init__(self, classifier, max_horses: int = 10):
        self._classifier = classifier
        self._feature_cols: list[str] = []
        super().__init__(max_horses)

    def _prepare_training_df(self, train_df: pd.DataFrame) -> pd.DataFrame:
        return train_df

    def _prepare_prediction_df(self, merged: pd.DataFrame) -> pd.DataFrame:
        return merged

    def _apply_gate(self, predictable: pd.DataFrame) -> pd.DataFrame:
        return predictable

    def _sample_weight(self, data: pd.DataFrame) -> np.ndarray | None:
        return None

    def _compute_win_scores(self, data: pd.DataFrame, feature_cols: list[str]) -> np.ndarray:
        return self._classifier.predict_proba(data[feature_cols])[:, 1]

    def fit(self, train_df: pd.DataFrame) -> None:
        df = self._prepare_training_df(train_df)
        df = _add_race_context(df, self.extra_nan_tolerant_features)

        extra = self.extra_nan_tolerant_features
        rel_extra = [f"Rel{c}" for c in extra if f"Rel{c}" in df.columns]
        feature_cols = REQUIRED_PREDICTORS + OPTIONAL_PREDICTORS + extra + rel_extra
        available = [c for c in feature_cols if c in df.columns]
        required = [c for c in REQUIRED_PREDICTORS if c in df.columns] + ["Wins"]

        label_cols = ["Wins"] + (["FinishingPosition"] if "FinishingPosition" in df.columns else [])
        data = df[available + label_cols].dropna(subset=required).copy()
        if "DaysRested" in data.columns:
            data.loc[data["DaysRested"] > 10, "DaysRested"] = 10
        if "DaysSinceJockeyLastRaced" in data.columns:
            data.loc[data["DaysSinceJockeyLastRaced"] > 10, "DaysSinceJockeyLastRaced"] = 10

        self._feature_cols = available
        sw = self._sample_weight(data)
        fit_kwargs = {"sample_weight": sw} if sw is not None else {}
        self._classifier.fit(data[available], data["Wins"], **fit_kwargs)

    def _run_prediction(
        self,
        races: pd.DataFrame,
        horse_stats: pd.DataFrame,
        jockey_stats: pd.DataFrame,
        trainer_stats: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """Returns full predictable field scored with WinProbability and PredictedRank."""
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

        if trainer_stats is not None:
            merged = pd.merge(merged, trainer_stats, how="left", on=["TrainerId"])

        merged = encode_surfaces(merged)
        merged = encode_going(merged)
        merged = encode_race_type(merged)
        merged = calculate_weight_change(merged)
        merged = calculate_distance_change(merged)
        merged = calculate_surface_switch(merged)
        merged = calculate_code_switch(merged)
        merged = calculate_race_class(merged)
        merged = calculate_age_features(merged)
        merged = encode_pattern(merged)
        merged = calculate_is_handicap(merged)
        merged = encode_age_band(merged)
        merged = encode_sex_restriction(merged)
        merged = encode_headgear(merged)
        merged = self._prepare_prediction_df(merged)
        merged = _add_race_context(merged, self.extra_nan_tolerant_features)
        merged = calculate_draw_features(merged)

        available = [c for c in self._feature_cols if c in merged.columns]
        required = [c for c in REQUIRED_PREDICTORS if c in available]
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

        predictable = self._apply_gate(predictable)

        if len(predictable) == 0:
            return pd.DataFrame(columns=["RaceId", "HorseId"])

        predictable["WinProbability"] = self._compute_win_scores(predictable, available)
        predictable["PredictedRank"] = predictable.groupby("RaceId")["WinProbability"].rank(
            method="dense", ascending=False
        )

        return predictable

    def predict_field(
        self,
        races: pd.DataFrame,
        horse_stats: pd.DataFrame,
        jockey_stats: pd.DataFrame,
        trainer_stats: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """Returns all horses in predictable races with WinProbability and PredictedRank."""
        return self._run_prediction(races, horse_stats, jockey_stats, trainer_stats)
