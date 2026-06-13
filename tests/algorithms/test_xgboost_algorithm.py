import pytest
import pandas as pd
from datetime import datetime

from race_analytics.algorithms.xgboost_algorithm import XGBoostAlgorithm
from race_analytics.features.race_data import RaceDataBuilder

_LONG_AGO = datetime(2020, 1, 1)
_AS_OF = datetime(2026, 1, 1)


def _fit(algo, rows):
    algo.fit(RaceDataBuilder().wrap_training(pd.DataFrame(rows)))
    return algo


def _serve(races, horse_stats, jockey_stats):
    return RaceDataBuilder().build_serving_from_stats(
        races, horse_stats, jockey_stats, None, as_of=_AS_OF
    )


def _train_row(race_id: int, horse_id: int, speed: float = 16.0) -> dict:
    return {
        "RaceId": race_id, "HorseId": horse_id, "Speed": speed,
        "DistanceInMeters": 1600.0, "WeightInPounds": 126.0,
        "Surface_AllWeather": 0.0, "Surface_Dirt": 0.0, "Surface_Turf": 1.0,
        "Going_Firm": 0.0, "Going_Good": 1.0, "Going_Good_To_Firm": 0.0,
        "Going_Good_To_Soft": 0.0, "Going_Heavy": 0.0, "Going_Soft": 0.0,
        "RaceType_Flat": 1.0, "RaceType_Hurdle": 0.0,
        "RaceType_Other": 0.0, "RaceType_SteepleChase": 0.0,
        "LastRaceDistanceInMeters": 1600.0, "LastRaceWeightInPounds": 126.0,
        "LastRaceSpeed": speed * 0.95, "DaysRested": 7.0,
        "LastRaceAvgRelFinishingPosition": 0.5,
        "LastRaceSurface_AllWeather": 0.0, "LastRaceSurface_Dirt": 0.0, "LastRaceSurface_Turf": 1.0,
        "LastRaceGoing_Good": 1.0, "LastRaceGoing_Good_To_Soft": 0.0, "LastRaceGoing_Soft": 0.0,
        "LastRaceGoing_Good_To_Firm": 0.0, "LastRaceGoing_Firm": 0.0, "LastRaceGoing_Heavy": 0.0,
        "LastRaceRaceType_Other": 0.0, "LastRaceRaceType_Hurdle": 0.0,
        "LastRaceRaceType_SteepleChase": 0.0, "LastRaceRaceType_Flat": 1.0,
        "JockeyNumberOfPriorRaces": 10.0, "DaysSinceJockeyLastRaced": 3.0,
        "JockeyWinPercentage": 0.2, "JockeyTop3Percentage": 0.5,
        "JockeyAvgRelFinishingPosition": 0.4,
    }


def _race_row(race_id: int, horse_id: int, jockey_id: int) -> dict:
    return {
        "RaceId": race_id, "HorseId": horse_id, "JockeyId": jockey_id,
        "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
        "DistanceInMeters": 1600.0, "WeightInPounds": 126.0,
    }


def _horse_stat(horse_id: int, last_race_speed: float = 16.0) -> dict:
    return {
        "HorseId": horse_id, "LastOff": _LONG_AGO,
        "LastRaceDistanceInMeters": 1600.0, "LastRaceWeightInPounds": 126.0,
        "LastRaceAvgRelFinishingPosition": 0.5, "LastRaceSpeed": last_race_speed,
        "LastRaceSurface_AllWeather": 0.0, "LastRaceSurface_Dirt": 0.0, "LastRaceSurface_Turf": 1.0,
        "LastRaceGoing_Firm": 0.0, "LastRaceGoing_Good": 1.0,
        "LastRaceGoing_Good_To_Firm": 0.0, "LastRaceGoing_Good_To_Soft": 0.0,
        "LastRaceGoing_Heavy": 0.0, "LastRaceGoing_Soft": 0.0,
        "LastRaceRaceType_Flat": 1.0, "LastRaceRaceType_Hurdle": 0.0,
        "LastRaceRaceType_Other": 0.0, "LastRaceRaceType_SteepleChase": 0.0,
    }


def _jockey_stat(jockey_id: int) -> dict:
    return {
        "JockeyId": jockey_id, "LastOff": _LONG_AGO,
        "JockeyNumberOfPriorRaces": 10.0,
        "JockeyWinPercentage": 0.2,
        "JockeyTop3Percentage": 0.5,
        "JockeyAvgRelFinishingPosition": 0.4,
    }


@pytest.fixture
def trained_algo() -> XGBoostAlgorithm:
    algo = XGBoostAlgorithm(max_horses=10)
    rows = [
        _train_row(race_id=r, horse_id=r * 10 + h, speed=14.0 + h)
        for r in range(1, 6) for h in range(3)
    ]
    return _fit(algo, rows)


# ================================================================
# Correct output columns and shape
# ================================================================


def test_predict_returns_raceId_and_horseId_columns(trained_algo):
    races = pd.DataFrame([_race_row(10, h, h) for h in [101, 102, 103]])
    horse_stats = pd.DataFrame([_horse_stat(h) for h in [101, 102, 103]])
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in [101, 102, 103]])

    result = trained_algo.predict(_serve(races, horse_stats, jockey_stats))

    assert list(result.columns) == ["RaceId", "HorseId"]


# ================================================================
# One winner per race
# ================================================================


def test_predict_returns_one_row_per_race(trained_algo):
    races = pd.DataFrame(
        [_race_row(10, h, h) for h in [101, 102, 103]]
        + [_race_row(20, h, h) for h in [201, 202, 203]]
    )
    horse_stats = pd.DataFrame(
        [_horse_stat(h) for h in [101, 102, 103, 201, 202, 203]]
    )
    jockey_stats = pd.DataFrame(
        [_jockey_stat(h) for h in [101, 102, 103, 201, 202, 203]]
    )

    result = trained_algo.predict(_serve(races, horse_stats, jockey_stats))

    assert len(result) == 2
    assert set(result["RaceId"]) == {10, 20}
    assert result["RaceId"].nunique() == len(result)


# ================================================================
# max_horses filter
# ================================================================


def test_predict_excludes_races_exceeding_max_horses():
    algo = XGBoostAlgorithm(max_horses=5)
    rows = [
        _train_row(race_id=r, horse_id=r * 10 + h)
        for r in range(1, 6) for h in range(3)
    ]
    _fit(algo, rows)

    all_ids = [101, 102, 103] + list(range(201, 208))
    race_rows = (
        [_race_row(10, h, h) for h in [101, 102, 103]]
        + [_race_row(20, h, h) for h in range(201, 208)]
    )

    result = algo.predict(_serve(
        pd.DataFrame(race_rows),
        pd.DataFrame([_horse_stat(h) for h in all_ids]),
        pd.DataFrame([_jockey_stat(h) for h in all_ids]),
    ))

    assert len(result) == 1
    assert result.iloc[0]["RaceId"] == 10
