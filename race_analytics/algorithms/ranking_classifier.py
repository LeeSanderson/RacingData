from typing import ClassVar

import numpy as np
import pandas as pd
from xgboost import XGBRanker

from race_analytics.algorithms.win_classifier import WinClassifier


class RankingClassifier(WinClassifier):
    """Learning-to-rank variant using XGBRanker with rank:pairwise objective.

    Labels: HorseCount - FinishingPosition + 1 (winner gets highest label).
    WinProbability stores the ranking score, not a calibrated probability.
    """

    label_col: ClassVar[str] = "FinishingPosition"

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

    def _fit_estimator(
        self, X: pd.DataFrame, frame: pd.DataFrame, sample_weight: np.ndarray | None
    ) -> None:
        data = frame.sort_values("RaceId")
        group_sizes = data.groupby("RaceId")["RaceId"].count().values
        labels = (data["HorseCount"] - data["FinishingPosition"] + 1).clip(lower=0)
        self._ranker.fit(data[self._feature_cols], labels, group=group_sizes)

    def _score(self, X: pd.DataFrame) -> np.ndarray:
        return self._ranker.predict(X)
