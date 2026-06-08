from datetime import timedelta

import numpy as np
import pandas as pd

from race_analytics.algorithms.win_classifier import WinClassifier


class RecencyWeightedWinClassifier(WinClassifier):
    """WinClassifier with exponential decay sample weighting.

    Recent races are weighted more heavily than stale ones.
    decay_lambda=0.01 gives half-weight at ~70 days.
    """

    def __init__(self, decay_lambda: float = 0.01, **kwargs):
        self._decay_lambda = decay_lambda
        self._decay_weights: pd.Series = pd.Series(dtype=float)
        super().__init__(**kwargs)

    def _prepare_training_df(self, train_df: pd.DataFrame) -> pd.DataFrame:
        df = super()._prepare_training_df(train_df)
        fold_date = pd.to_datetime(train_df["Off"]).max().date() + timedelta(days=1)
        race_dates = pd.to_datetime(train_df["Off"]).dt.date
        days_ago = np.array([(fold_date - d).days for d in race_dates])
        self._decay_weights = pd.Series(
            np.exp(-self._decay_lambda * days_ago),
            index=train_df.index,
        )
        return df

    def _sample_weight(self, data: pd.DataFrame) -> np.ndarray | None:
        if self._decay_weights.empty:
            return None
        return self._decay_weights.loc[data.index].to_numpy()
