from abc import ABC, abstractmethod
from typing import ClassVar
import pandas as pd

REQUIRED_PREDICTORS = [
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
    "TrainerNumberOfPriorRaces",
    "TrainerWinPercentage",
    "TrainerTop3Percentage",
    "TrainerAvgRelFinishingPosition",
    "IsFirstTimeHeadgear",
    "HasBlinkers",
    "HasCheekpieces",
    "HasTongueTie",
    "HasHood",
    "HasVisor",
    "HeadGearChanged",
]

OPTIONAL_PREDICTORS = [
    "Last3RaceAvgSpeed",
    "Last3RaceSpeedTrend",
    "Last3AvgRelFinishingPosition",
    "WeightChange",
    "DistanceChange",
    "HorseCount",
    "SurfaceSwitch",
    "CodeSwitch",
    "RaceClass",
    "Age",
    "RelAge",
    "DrawPct",
    "RelDraw",
    "IsHandicap",
    "Pattern_Group1",
    "Pattern_Group2",
    "Pattern_Group3",
    "Pattern_Listed",
    "Pattern_None",
    "AgeBand_2yo",
    "AgeBand_3yo",
    "AgeBand_3yoPlus",
    "AgeBand_4yoPlus",
    "AgeBand_None",
    "SexRestriction_F",
    "SexRestriction_FM",
    "SexRestriction_Open",
]

PREDICTORS = REQUIRED_PREDICTORS + OPTIONAL_PREDICTORS


class BaseAlgorithm(ABC):
    nan_tolerant_predictors: ClassVar[list[str]] = []

    def __init__(self, max_horses: int = 10):
        self.max_horses = max_horses

    @abstractmethod
    def fit(self, train_df: pd.DataFrame) -> None: ...

    @abstractmethod
    def predict(
        self,
        races: pd.DataFrame,
        horse_stats: pd.DataFrame,
        jockey_stats: pd.DataFrame,
        trainer_stats: pd.DataFrame | None = None,
    ) -> pd.DataFrame: ...


class FieldPredictorBaseAlgorithm(BaseAlgorithm):
    """
    Extension of BaseAlgorithm for algorithms that can produce a prediction field with WinProbability and PredictedRank
    for each horse in each race. This allows for more nuanced predictions and the ability to apply gating strategies based
    on confidence or other criteria.
    """

    @abstractmethod
    def predict_field(
        self,
        races: pd.DataFrame,
        horse_stats: pd.DataFrame,
        jockey_stats: pd.DataFrame,
        trainer_stats: pd.DataFrame | None = None,
    ) -> pd.DataFrame: ...

    def predict(
        self,
        races: pd.DataFrame,
        horse_stats: pd.DataFrame,
        jockey_stats: pd.DataFrame,
        trainer_stats: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        field = self.predict_field(races, horse_stats, jockey_stats, trainer_stats)
        if field.empty or "PredictedRank" not in field.columns:
            return pd.DataFrame(columns=["RaceId", "HorseId"])
        return (
            field[field["PredictedRank"] == 1][["RaceId", "HorseId"]]
            .drop_duplicates(subset=["RaceId"])
            .reset_index(drop=True)
        )
