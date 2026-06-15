from abc import abstractmethod
from typing import ClassVar

import numpy as np
import pandas as pd

from race_analytics.algorithms.base import (
    FieldPredictorBaseAlgorithm,
    PREDICTORS,
    REQUIRED_PREDICTORS,
)
from race_analytics.features.race_data import RaceData


class RegressorAlgorithm(FieldPredictorBaseAlgorithm):
    """Speed regressor on the shared RaceData engine.

    Flips the engine conventions to regression: trains on `Speed`, scores with
    `PredictedSpeed`, and returns a single top-1 pick per race. Feature selection is
    the regressor's own two-tier rule — every required predictor plus only the
    `nan_tolerant_predictors` (so a plain regressor uses no optional features, while
    one that opts in tolerates their NaNs). The merge/encode/complete-race/rank
    data-path lives in the base engine and `RaceDataBuilder`.
    """

    label_col: ClassVar[str] = "Speed"
    score_col: ClassVar[str] = "PredictedSpeed"
    return_full_field: ClassVar[bool] = False

    def __init__(self, max_horses: int = 10):
        super().__init__(max_horses)
        self._model = self._create_model()
        self._fitted_predictors: list[str] = list(PREDICTORS)

    @abstractmethod
    def _create_model(self):
        ...

    def _select_features(self, data: RaceData) -> list[str]:
        required = [c for c in REQUIRED_PREDICTORS if c in data.frame.columns]
        tolerated = [c for c in self.nan_tolerant_predictors if c in data.frame.columns]
        self._fitted_predictors = required + tolerated
        return self._fitted_predictors

    def _fit_estimator(self, X: pd.DataFrame, frame: pd.DataFrame, sample_weight) -> None:
        self._model.fit(X, frame[self.label_col])

    def _score(self, X: pd.DataFrame) -> np.ndarray:
        return self._model.predict(X)
