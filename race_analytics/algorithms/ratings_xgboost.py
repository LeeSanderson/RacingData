from datetime import datetime
import numpy as np
import pandas as pd
from xgboost import XGBClassifier

from race_analytics.algorithms.base import BaseAlgorithm, PREDICTORS
from race_analytics.features.transforms import encode_surfaces, encode_going, encode_race_type

RATING_COLS = ["OfficialRating", "RacingPostRating", "TopSpeedRating"]


def _add_race_context(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "HorseCount" not in df.columns:
        df["HorseCount"] = df.groupby("RaceId")["HorseId"].transform("count")
    for col in RATING_COLS:
        if col in df.columns:
            df[f"Rel{col}"] = df[col] - df.groupby("RaceId")[col].transform("mean")
    return df


class RatingsXGBoostAlgorithm(BaseAlgorithm):
    def __init__(self, max_horses: int = 10, require_tsr: bool = True):
        self._require_tsr = require_tsr
        self._classifier = XGBClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=4,
            random_state=42,
            verbosity=0,
            eval_metric="logloss",
        )
        super().__init__(max_horses)

    def _create_model(self) -> XGBClassifier:
        return self._classifier

    def fit(self, train_df: pd.DataFrame) -> None:
        df = _add_race_context(train_df)
        rel_cols = [f"Rel{c}" for c in RATING_COLS if f"Rel{c}" in df.columns]
        abs_cols = [c for c in RATING_COLS if c in df.columns]
        feature_cols = PREDICTORS + abs_cols + rel_cols + ["HorseCount"]
        available = [c for c in feature_cols if c in df.columns]
        # Require only PREDICTORS and Wins to be non-null; ratings may be NaN
        # (XGBoost handles missing values natively via learned split directions)
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
        trainer_stats: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        if not getattr(self, "_feature_cols", None):
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
        merged = _add_race_context(merged)

        available = [c for c in self._feature_cols if c in merged.columns]
        # Only require PREDICTORS to be non-null; ratings may be NaN
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

        if self._require_tsr and "TopSpeedRating" in predictable.columns:
            tsr_complete = predictable.groupby("RaceId")["TopSpeedRating"].transform(
                lambda x: x.notna().all()
            )
            predictable = predictable[tsr_complete].copy()

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


class RatingsXGBoostUngatedAlgorithm(RatingsXGBoostAlgorithm):
    """RatingsXGBoostAlgorithm without the TSR-complete filter, for comparison."""
    def __init__(self, max_horses: int = 10):
        super().__init__(max_horses, require_tsr=False)
