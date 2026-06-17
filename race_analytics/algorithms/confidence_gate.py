import numpy as np
import pandas as pd


class ConfidenceGate:
    """Pure confidence gate: keep/abstain per race from per-horse win probabilities."""

    def __init__(self, metric: str = "top_prob"):
        if metric not in ("top_prob", "gap"):
            raise ValueError(f"metric must be 'top_prob' or 'gap', got {metric!r}")
        self.metric = metric
        self.threshold: float = 0.0
        self._calib_scores: list[float] = []

    def score(self, probs: pd.Series) -> float:
        """Confidence score for a race. Returns 0.0 for empty race."""
        if len(probs) == 0:
            return 0.0
        sorted_p = sorted(probs, reverse=True)
        if self.metric == "top_prob":
            return float(sorted_p[0])
        second = sorted_p[1] if len(sorted_p) > 1 else 0.0
        return float(sorted_p[0] - second)

    def calibrate(self, scores: list[float], coverage: float) -> None:
        """Set threshold so `coverage` fraction of training races are kept.

        threshold = (1 - coverage) quantile of scores.
        Scores are stored for later frontier sweeping.
        """
        self._calib_scores = list(scores)
        if not scores:
            self.threshold = 0.0
            return
        self.threshold = float(np.quantile(scores, 1.0 - coverage))

    def keep(self, score: float) -> bool:
        return float(score) >= self.threshold
