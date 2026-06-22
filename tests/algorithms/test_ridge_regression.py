from datetime import datetime

import pandas as pd
import pytest

from race_analytics.algorithms.ridge_regression import RidgeRegressionAlgorithm
from race_analytics.features.race_data import RaceData, RaceDataBuilder

# A fixed past date so DaysRested always caps at 10 — keeps tests deterministic
_LONG_AGO = datetime(2020, 1, 1)
_AS_OF = datetime(2026, 1, 1)


def _fit(
    algo: RidgeRegressionAlgorithm, rows: list[dict[str, object]]
) -> RidgeRegressionAlgorithm:
    algo.fit(RaceDataBuilder().wrap_training(pd.DataFrame(rows)))
    return algo


def _serve(
    races: pd.DataFrame, horse_stats: pd.DataFrame, jockey_stats: pd.DataFrame
) -> RaceData:
    return RaceDataBuilder().build_serving_from_stats(
        races,
        horse_stats,
        jockey_stats,
        None,
        as_of=_AS_OF,  # pyright: ignore[reportArgumentType]  # pd.Timestamp accepts a datetime at runtime
    )


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
]


def _train_row(race_id: int, horse_id: int, speed: float = 16.0) -> dict[str, object]:
    """Fully-specified training row with all predictor columns + Speed."""
    return {
        "RaceId": race_id,
        "HorseId": horse_id,
        "Speed": speed,
        "DistanceInMeters": 1600.0,
        "WeightInPounds": 126.0,
        "Surface_AllWeather": 0.0,
        "Surface_Dirt": 0.0,
        "Surface_Turf": 1.0,
        "Going_Firm": 0.0,
        "Going_Good": 1.0,
        "Going_Good_To_Firm": 0.0,
        "Going_Good_To_Soft": 0.0,
        "Going_Heavy": 0.0,
        "Going_Soft": 0.0,
        "RaceType_Flat": 1.0,
        "RaceType_Hurdle": 0.0,
        "RaceType_Other": 0.0,
        "RaceType_SteepleChase": 0.0,
        "LastRaceDistanceInMeters": 1600.0,
        "LastRaceWeightInPounds": 126.0,
        "LastRaceSpeed": speed * 0.95,
        "DaysRested": 7.0,
        "LastRaceAvgRelFinishingPosition": 0.5,
        "LastRaceSurface_AllWeather": 0.0,
        "LastRaceSurface_Dirt": 0.0,
        "LastRaceSurface_Turf": 1.0,
        "LastRaceGoing_Good": 1.0,
        "LastRaceGoing_Good_To_Soft": 0.0,
        "LastRaceGoing_Soft": 0.0,
        "LastRaceGoing_Good_To_Firm": 0.0,
        "LastRaceGoing_Firm": 0.0,
        "LastRaceGoing_Heavy": 0.0,
        "LastRaceRaceType_Other": 0.0,
        "LastRaceRaceType_Hurdle": 0.0,
        "LastRaceRaceType_SteepleChase": 0.0,
        "LastRaceRaceType_Flat": 1.0,
        "JockeyNumberOfPriorRaces": 10.0,
        "DaysSinceJockeyLastRaced": 3.0,
        "JockeyWinPercentage": 0.2,
        "JockeyTop3Percentage": 0.5,
        "JockeyAvgRelFinishingPosition": 0.4,
    }


def _race_row(race_id: int, horse_id: int, jockey_id: int) -> dict[str, object]:
    return {
        "RaceId": race_id,
        "HorseId": horse_id,
        "JockeyId": jockey_id,
        "Surface": "Turf",
        "Going": "Good",
        "RaceType": "Flat",
        "DistanceInMeters": 1600.0,
        "WeightInPounds": 126.0,
    }


def _horse_stat(horse_id: int, last_race_speed: float = 16.0) -> dict[str, object]:
    return {
        "HorseId": horse_id,
        "LastOff": _LONG_AGO,
        "LastRaceDistanceInMeters": 1600.0,
        "LastRaceWeightInPounds": 126.0,
        "LastRaceAvgRelFinishingPosition": 0.5,
        "LastRaceSpeed": last_race_speed,
        "LastRaceSurface_AllWeather": 0.0,
        "LastRaceSurface_Dirt": 0.0,
        "LastRaceSurface_Turf": 1.0,
        "LastRaceGoing_Firm": 0.0,
        "LastRaceGoing_Good": 1.0,
        "LastRaceGoing_Good_To_Firm": 0.0,
        "LastRaceGoing_Good_To_Soft": 0.0,
        "LastRaceGoing_Heavy": 0.0,
        "LastRaceGoing_Soft": 0.0,
        "LastRaceRaceType_Flat": 1.0,
        "LastRaceRaceType_Hurdle": 0.0,
        "LastRaceRaceType_Other": 0.0,
        "LastRaceRaceType_SteepleChase": 0.0,
    }


def _jockey_stat(jockey_id: int) -> dict[str, object]:
    return {
        "JockeyId": jockey_id,
        "LastOff": _LONG_AGO,
        "JockeyNumberOfPriorRaces": 10.0,
        "JockeyWinPercentage": 0.2,
        "JockeyTop3Percentage": 0.5,
        "JockeyAvgRelFinishingPosition": 0.4,
    }


@pytest.fixture
def trained_algo() -> RidgeRegressionAlgorithm:
    """Fitted algorithm: 5 races x 3 horses, speeds vary 14-16."""
    algo = RidgeRegressionAlgorithm(max_horses=10)
    rows = [
        _train_row(race_id=r, horse_id=r * 10 + h, speed=14.0 + h)
        for r in range(1, 6)
        for h in range(3)
    ]
    return _fit(algo, rows)


def test_predict_returns_raceId_and_horseId_columns(
    trained_algo: RidgeRegressionAlgorithm,
) -> None:
    races = pd.DataFrame([_race_row(10, h, h) for h in [101, 102, 103]])
    horse_stats = pd.DataFrame([_horse_stat(h) for h in [101, 102, 103]])
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in [101, 102, 103]])

    result = trained_algo.predict(_serve(races, horse_stats, jockey_stats))

    assert list(result.columns) == ["RaceId", "HorseId"]


def test_predict_returns_one_row_per_race(
    trained_algo: RidgeRegressionAlgorithm,
) -> None:
    races = pd.DataFrame(
        [_race_row(10, h, h) for h in [101, 102, 103]]
        + [_race_row(20, h, h) for h in [201, 202, 203]]
    )
    horse_stats = pd.DataFrame([_horse_stat(h) for h in [101, 102, 103, 201, 202, 203]])
    jockey_stats = pd.DataFrame(
        [_jockey_stat(h) for h in [101, 102, 103, 201, 202, 203]]
    )

    result = trained_algo.predict(_serve(races, horse_stats, jockey_stats))

    assert len(result) == 2
    assert set(result["RaceId"]) == {10, 20}
    assert result["RaceId"].nunique() == len(result)


def test_predict_excludes_races_exceeding_max_horses() -> None:
    algo = RidgeRegressionAlgorithm(max_horses=5)
    rows = [
        _train_row(race_id=r, horse_id=r * 10 + h)
        for r in range(1, 6)
        for h in range(3)
    ]
    _fit(algo, rows)

    all_ids = [101, 102, 103, *range(201, 208)]
    race_rows = [_race_row(10, h, h) for h in [101, 102, 103]] + [
        _race_row(20, h, h) for h in range(201, 208)
    ]

    result = algo.predict(
        _serve(
            pd.DataFrame(race_rows),
            pd.DataFrame([_horse_stat(h) for h in all_ids]),
            pd.DataFrame([_jockey_stat(h) for h in all_ids]),
        )
    )

    assert len(result) == 1
    assert result.iloc[0]["RaceId"] == 10
