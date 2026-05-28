from abc import ABC, abstractmethod
from typing import Any, Protocol
import numpy as np
import pandas as pd


class _Estimator(Protocol):
    def fit(self, X: Any, y: Any) -> Any: ...
    def predict(self, X: Any) -> np.ndarray: ...

PREDICTORS = [
    "DistanceInMeters",
    "WeightInPounds",
    "Surface_AllWeather",
    "Surface_Dirt",
    "Surface_Turf",
    "Going_Firm",
    "Going_Good",
    "Going_Good_To_Firm",
    "Going_Good_To_Soft",
    "Going_Heavy",
    "Going_Soft",
    "RaceType_Flat",
    "RaceType_Hurdle",
    "RaceType_Other",
    "RaceType_SteepleChase",
    "LastRaceDistanceInMeters",
    "LastRaceWeightInPounds",
    "LastRaceSpeed",
    "DaysRested",
    "LastRaceAvgRelFinishingPosition",
    "LastRaceSurface_AllWeather",
    "LastRaceSurface_Dirt",
    "LastRaceSurface_Turf",
    "LastRaceGoing_Good",
    "LastRaceGoing_Good_To_Soft",
    "LastRaceGoing_Soft",
    "LastRaceGoing_Good_To_Firm",
    "LastRaceGoing_Firm",
    "LastRaceGoing_Heavy",
    "LastRaceRaceType_Other",
    "LastRaceRaceType_Hurdle",
    "LastRaceRaceType_SteepleChase",
    "LastRaceRaceType_Flat",
    "JockeyNumberOfPriorRaces",
    "DaysSinceJockeyLastRaced",
    "JockeyWinPercentage",
    "JockeyTop3Percentage",
    "JockeyAvgRelFinishingPosition",
    "Last3RaceAvgSpeed",
    "Last3RaceSpeedTrend",
    "Last3AvgRelFinishingPosition",
    "TrainerNumberOfPriorRaces",
    "TrainerWinPercentage",
    "TrainerTop3Percentage",
    "TrainerAvgRelFinishingPosition",
]


class BaseAlgorithm(ABC):
    def __init__(self, max_horses: int = 10):
        self.max_horses = max_horses

    @abstractmethod
    def fit(self, train_df: pd.DataFrame) -> None:
        ...

    @abstractmethod
    def predict(
        self,
        races: pd.DataFrame,
        horse_stats: pd.DataFrame,
        jockey_stats: pd.DataFrame,
        trainer_stats: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        ...
