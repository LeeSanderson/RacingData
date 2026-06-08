import numpy as np
import pandas as pd
from xgboost import XGBRanker

from race_analytics.algorithms.base import OPTIONAL_PREDICTORS, REQUIRED_PREDICTORS
from race_analytics.algorithms.binary_win_classifier import _add_race_context
from race_analytics.algorithms.win_classifier import WinClassifier


class RankingClassifier(WinClassifier):
    """Learning-to-rank variant using XGBRanker with rank:pairwise objective.

    Labels: HorseCount − FinishingPosition + 1 (winner gets highest label).
    WinProbability stores the ranking score, not a calibrated probability.
    """

    def __init__(self, max_horses: int = 10):
        super().__init__(max_horses=max_horses)
        self._ranker = XGBRanker(
            objective="rank:pairwise",
            n_estimators=200,
            learning_rate=0.05,
            max_depth=4,
            random_state=42,
            verbosity=0,
        )

    def _compute_win_scores(self, data: pd.DataFrame, feature_cols: list[str]) -> np.ndarray:
        return self._ranker.predict(data[feature_cols])

    def fit(self, train_df: pd.DataFrame) -> None:
        df = self._prepare_training_df(train_df)
        df = _add_race_context(df, self.extra_nan_tolerant_features)

        extra = self.extra_nan_tolerant_features
        rel_extra = [f"Rel{c}" for c in extra if f"Rel{c}" in df.columns]
        feature_cols = REQUIRED_PREDICTORS + OPTIONAL_PREDICTORS + extra + rel_extra
        available = [c for c in feature_cols if c in df.columns]
        required = [c for c in REQUIRED_PREDICTORS if c in df.columns] + ["FinishingPosition"]

        meta = [c for c in ["RaceId", "HorseCount", "FinishingPosition"] if c in df.columns]
        extra_meta = [c for c in meta if c not in available]
        data = df[available + extra_meta].dropna(subset=required).copy()

        if "DaysRested" in data.columns:
            data.loc[data["DaysRested"] > 10, "DaysRested"] = 10
        if "DaysSinceJockeyLastRaced" in data.columns:
            data.loc[data["DaysSinceJockeyLastRaced"] > 10, "DaysSinceJockeyLastRaced"] = 10

        self._feature_cols = available
        data = data.sort_values("RaceId")
        group_sizes = data.groupby("RaceId")["RaceId"].count().values
        labels = (data["HorseCount"] - data["FinishingPosition"] + 1).clip(lower=0)
        self._ranker.fit(data[available], labels, group=group_sizes)
