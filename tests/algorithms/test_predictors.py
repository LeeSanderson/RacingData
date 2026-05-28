from race_analytics.algorithms.base import PREDICTORS

_NEW_COLS = [
    "Last3RaceAvgSpeed",
    "Last3RaceSpeedTrend",
    "Last3AvgRelFinishingPosition",
    "TrainerNumberOfPriorRaces",
    "TrainerWinPercentage",
    "TrainerTop3Percentage",
    "TrainerAvgRelFinishingPosition",
]


def test_predictors_contains_new_columns():
    for col in _NEW_COLS:
        assert col in PREDICTORS, f"Missing predictor: {col}"
