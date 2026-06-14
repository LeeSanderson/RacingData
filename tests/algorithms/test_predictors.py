from race_analytics.algorithms.base import (
    OPTIONAL_PREDICTORS,
    PREDICTORS,
    REQUIRED_PREDICTORS,
)

_NEW_COLS = [
    "Last3RaceAvgSpeed",
    "Last3RaceSpeedTrend",
    "Last3AvgRelFinishingPosition",
    "TrainerNumberOfPriorRaces",
    "TrainerWinPercentage",
    "TrainerTop3Percentage",
    "TrainerAvgRelFinishingPosition",
]

_OPTIONAL_COLS = [
    "Last3RaceAvgSpeed",
    "Last3RaceSpeedTrend",
    "Last3AvgRelFinishingPosition",
    "WeightChange",
    "DistanceChange",
    "HorseCount",
    "SurfaceSwitch",
    "CodeSwitch",
]


def test_predictors_contains_new_columns():
    for col in _NEW_COLS:
        assert col in PREDICTORS, f"Missing predictor: {col}"


def test_optional_predictors_include_nan_tolerant_features():
    for col in _OPTIONAL_COLS:
        assert col in OPTIONAL_PREDICTORS, f"Missing optional predictor: {col}"


def test_required_predictors_excludes_last3_columns():
    for col in _OPTIONAL_COLS:
        assert col not in REQUIRED_PREDICTORS


def test_predictors_is_required_plus_optional():
    assert PREDICTORS == REQUIRED_PREDICTORS + OPTIONAL_PREDICTORS
