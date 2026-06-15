import numpy as np
import pandas as pd

from race_analytics.algorithms.win_classifier import WinClassifier
from race_analytics.features.race_data import RaceData


class RecencyWeightedWinClassifier(WinClassifier):
    """WinClassifier with exponential decay sample weighting.

    Recent races are weighted more heavily than stale ones. Decay is measured from
    `RaceData.as_of` (the fold date) — never the wall clock — so the weights depend
    only on the data window, not on when fit() happens to run.
    decay_lambda=0.01 gives half-weight at ~70 days.
    """

    def __init__(self, decay_lambda: float = 0.01, **kwargs):
        self._decay_lambda = decay_lambda
        super().__init__(**kwargs)

    def _prepare_training(self, data: RaceData) -> RaceData:
        data = super()._prepare_training(data)
        days_ago = (
            data.as_of.normalize() - pd.to_datetime(data.frame["Off"]).dt.normalize()
        ).dt.days
        return data.with_columns(_w=np.exp(-self._decay_lambda * days_ago))

    def _sample_weight(self, frame: pd.DataFrame) -> np.ndarray | None:
        if "_w" not in frame.columns:
            return None
        return frame["_w"].to_numpy()
