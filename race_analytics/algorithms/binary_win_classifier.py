from typing import ClassVar

import numpy as np
import pandas as pd

from race_analytics.algorithms.base import FieldPredictorBaseAlgorithm
from race_analytics.features.race_data import RaceData


class BinaryWinClassifierAlgorithm(FieldPredictorBaseAlgorithm):
    """Win-probability classifier on the shared RaceData engine.

    Supplies only what varies for a binary win classifier: the injected estimator's
    fit/score and the HorseCount + relative-rating race context. The merge/encode,
    complete-race filter, and within-race ranking all live in the base engine and
    `RaceDataBuilder`.
    """

    extra_nan_tolerant_features: ClassVar[list[str]] = []

    def __init__(self, classifier, max_horses: int = 10):
        self._classifier = classifier
        super().__init__(max_horses)

    def _prepare_training(self, data: RaceData) -> RaceData:
        return self._add_race_context(data)

    def _prepare_serving(self, data: RaceData) -> RaceData:
        return self._add_race_context(data)

    def _fit_estimator(self, X: pd.DataFrame, frame: pd.DataFrame, sample_weight) -> None:
        fit_kwargs = {"sample_weight": sample_weight} if sample_weight is not None else {}
        self._classifier.fit(X, frame[self.label_col], **fit_kwargs)

    def _score(self, X: pd.DataFrame) -> np.ndarray:
        return self._classifier.predict_proba(X)[:, 1]
