from race_analytics.algorithms.base import PREDICTORS, REQUIRED_PREDICTORS, OPTIONAL_PREDICTORS

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
]


def test_predictors_contains_new_columns():
    for col in _NEW_COLS:
        assert col in PREDICTORS, f"Missing predictor: {col}"


def test_optional_predictors_are_last3_columns():
    assert OPTIONAL_PREDICTORS == _OPTIONAL_COLS


def test_required_predictors_excludes_last3_columns():
    for col in _OPTIONAL_COLS:
        assert col not in REQUIRED_PREDICTORS


def test_predictors_is_required_plus_optional():
    assert PREDICTORS == REQUIRED_PREDICTORS + OPTIONAL_PREDICTORS
