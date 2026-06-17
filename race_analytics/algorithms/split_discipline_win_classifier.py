import pandas as pd

from race_analytics.algorithms.base import FieldPredictorBaseAlgorithm
from race_analytics.algorithms.win_classifier import WinClassifier
from race_analytics.features.race_data import RaceData


class SplitDisciplineWinClassifier(WinClassifier):
    """WinClassifier with separate flat and jump sub-models.

    Trains distinct WinClassifier instances for flat and jump races, routing
    each prediction to the appropriate sub-model. Falls back to a model trained
    on all data when a sub-model has fewer than MIN_RACES unique races.

    The inner_class parameter allows cross-axis composition (e.g. wrapping a
    RecencyWeightedWinClassifier for each discipline sub-model).

    Splitting a `RaceData` keeps whole races together — a race is wholly flat or wholly
    jumps — so a discipline subset is identical to building the sub-frame from scratch,
    and the per-race feature columns are unchanged.
    """

    MIN_RACES = 100

    def __init__(
        self,
        inner_class: type[FieldPredictorBaseAlgorithm] = WinClassifier,
        max_horses: int = 10,
    ):
        super().__init__(max_horses=max_horses)
        self._flat_model = inner_class(max_horses=max_horses)
        self._jumps_model = inner_class(max_horses=max_horses)
        self._fallback_model = inner_class(max_horses=max_horses)
        self._flat_available = False
        self._jumps_available = False

    def fit(self, data: RaceData) -> None:
        flat_mask = self._flat_mask(data.frame)
        flat = data.subset(flat_mask)
        jumps = data.subset(~flat_mask)

        self._flat_available = (
            flat.frame["RaceId"].nunique() >= self.MIN_RACES
            if not flat.frame.empty
            else False
        )
        self._jumps_available = (
            jumps.frame["RaceId"].nunique() >= self.MIN_RACES
            if not jumps.frame.empty
            else False
        )

        if self._flat_available:
            self._flat_model.fit(flat)
        if self._jumps_available:
            self._jumps_model.fit(jumps)
        if not self._flat_available or not self._jumps_available:
            self._fallback_model.fit(data)

        super().fit(data)

    @staticmethod
    def _flat_mask(frame: pd.DataFrame) -> pd.Series:
        """Boolean per-row mask selecting flat races. Prefers the encoded
        RaceType_Flat one-hot, falling back to the raw RaceType string."""
        if "RaceType_Flat" in frame.columns:
            return frame["RaceType_Flat"] == 1
        if "RaceType" in frame.columns:
            return frame["RaceType"] == "Flat"
        return pd.Series(False, index=frame.index)

    def predict_field(self, data: RaceData) -> pd.DataFrame:
        frame = data.frame
        if "RaceType" not in frame.columns and "RaceType_Flat" not in frame.columns:
            return self._fallback_model.predict_field(data)

        flat_mask = self._flat_mask(frame)
        parts = []
        if flat_mask.any():
            m = self._flat_model if self._flat_available else self._fallback_model
            parts.append(m.predict_field(data.subset(flat_mask)))
        if (~flat_mask).any():
            m = self._jumps_model if self._jumps_available else self._fallback_model
            parts.append(m.predict_field(data.subset(~flat_mask)))

        non_empty = [p for p in parts if not p.empty]
        if not non_empty:
            return self._empty()
        return pd.concat(non_empty, ignore_index=True)
