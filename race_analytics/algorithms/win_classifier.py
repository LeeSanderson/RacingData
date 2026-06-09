from datetime import timedelta
from typing import ClassVar

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

from race_analytics.algorithms.base import OPTIONAL_PREDICTORS
from race_analytics.algorithms.binary_win_classifier import BinaryWinClassifierAlgorithm
from race_analytics.algorithms.proxy_tsr import ProxyTSRModel

# Previous-race ratings sourced from the per-horse stats join (leak-free); the
# current-race OfficialRating/RacingPostRating/TopSpeedRating are post-race
# figures and must never enter the model — see issues/prd.md.
RATING_COLS = [
    "LastRaceOfficialRating",
    "LastRaceRacingPostRating",
    "LastRaceTopSpeedRating",
]
# Single as-of-date proxy: the horse's last prior proxy TSR (no whole-window
# Peak/Best5 aggregate, which let a training row see the horse's future races).
PROXY_TSR_COLS = ["LastProxyTSR"]


class WinClassifier(BinaryWinClassifierAlgorithm):
    """XGBoost win-probability classifier using proxy TSR features.

    Trains a ProxyTSRModel alongside the main classifier so predictions are
    available for all horses, not only those with a Racing Post TopSpeedRating.
    No TSR gating is applied — all KnownHorseAndJockey races are predicted.
    """

    nan_tolerant_predictors = OPTIONAL_PREDICTORS
    extra_nan_tolerant_features: ClassVar[list[str]] = RATING_COLS + PROXY_TSR_COLS

    def __init__(
        self,
        max_horses: int = 10,
        n_estimators: int = 200,
        learning_rate: float = 0.05,
        max_depth: int = 4,
        subsample: float = 1.0,
        colsample_bytree: float = 1.0,
        tune_proxy: bool = False,
    ):
        self._tune_proxy = tune_proxy
        self._proxy_model = ProxyTSRModel()
        self._horse_proxy_tsr: pd.DataFrame = pd.DataFrame()
        super().__init__(
            XGBClassifier(
                n_estimators=n_estimators,
                learning_rate=learning_rate,
                max_depth=max_depth,
                subsample=subsample,
                colsample_bytree=colsample_bytree,
                random_state=42,
                verbosity=0,
                eval_metric="logloss",
            ),
            max_horses,
        )

    def _prepare_training_df(self, train_df: pd.DataFrame) -> pd.DataFrame:
        if self._tune_proxy:
            self._proxy_model.tune(train_df)
        self._proxy_model.fit(train_df)
        self._horse_proxy_tsr = self._proxy_model.compute_horse_proxy_tsr(train_df)
        df = train_df.copy()
        df["LastProxyTSR"] = self._proxy_model.compute_as_of_proxy(train_df)
        return df

    def _prepare_prediction_df(self, merged: pd.DataFrame) -> pd.DataFrame:
        if not self._horse_proxy_tsr.empty:
            merged = pd.merge(merged, self._horse_proxy_tsr, on="HorseId", how="left")
        return merged
