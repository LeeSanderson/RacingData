from typing import ClassVar

import pandas as pd
from xgboost import XGBClassifier

from race_analytics.algorithms.base import OPTIONAL_PREDICTORS
from race_analytics.algorithms.binary_win_classifier import BinaryWinClassifierAlgorithm

# Previous-race ratings sourced from the per-horse stats join (leak-free).
# The current-race OfficialRating/RacingPostRating/TopSpeedRating are post-race
# figures and must never enter the model — see issues/prd.md.
RATING_COLS = [
    "LastRaceOfficialRating",
    "LastRaceRacingPostRating",
    "LastRaceTopSpeedRating",
]


class RatingsXGBoostAlgorithm(BinaryWinClassifierAlgorithm):
    nan_tolerant_predictors = OPTIONAL_PREDICTORS
    extra_nan_tolerant_features: ClassVar[list[str]] = RATING_COLS

    def __init__(self, max_horses: int = 10):
        super().__init__(
            XGBClassifier(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=4,
                random_state=42,
                verbosity=0,
                eval_metric="logloss",
            ),
            max_horses,
        )

    def _apply_gate(self, predictable: pd.DataFrame) -> pd.DataFrame:
        """Keep only races where every horse has a LastRaceTopSpeedRating."""
        if "LastRaceTopSpeedRating" not in predictable.columns:
            return predictable
        tsr_complete = predictable.groupby("RaceId")["LastRaceTopSpeedRating"].transform(
            lambda x: x.notna().all()
        )
        return predictable[tsr_complete].copy()


class RatingsXGBoostUngatedAlgorithm(RatingsXGBoostAlgorithm):
    """RatingsXGBoostAlgorithm without the TSR-complete filter, for comparison."""

    def _apply_gate(self, predictable: pd.DataFrame) -> pd.DataFrame:
        return predictable
