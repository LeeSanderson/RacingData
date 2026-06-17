import numpy as np
import pandas as pd

from race_analytics.algorithms.win_classifier import WinClassifier


class PositionWeightedWinClassifier(WinClassifier):
    """WinClassifier with position-based sample weighting.

    Training samples are weighted by 1/FinishingPosition (winner=1.0, 2nd=0.5, …).
    """

    def _sample_weight(self, frame: pd.DataFrame) -> np.ndarray | None:
        if "FinishingPosition" not in frame.columns:
            return None
        return (1.0 / frame["FinishingPosition"]).to_numpy()
