"""Characterization of the regressor data-path (issue 005).

Pins the top-1 output of the merge → clamp → encode → complete-race → rank pipeline
*before* `RegressorAlgorithm` is moved onto the RaceData engine, so the migration can
be proven behaviour-preserving. A deterministic fake model (PredictedSpeed = the
horse's LastRaceSpeed) makes the ranking exact, so the assertions pin the data-path
itself, not an estimator's internals.
"""

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from race_analytics.algorithms.regressor import RegressorAlgorithm
from race_analytics.features.race_data import RaceData, RaceDataBuilder

_LONG_AGO = datetime(2020, 1, 1)
_AS_OF = datetime(2026, 1, 1)


def _rd(df: pd.DataFrame) -> RaceData:
    return RaceDataBuilder().wrap_training(df)


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


class _RankByLastRaceSpeed:
    """Fake regressor: PredictedSpeed == the row's LastRaceSpeed (higher ranks first)."""

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "_RankByLastRaceSpeed":
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return pd.DataFrame(X)["LastRaceSpeed"].to_numpy()


class _CharacterizationRegressor(RegressorAlgorithm):
    def _create_model(self) -> Any:
        return _RankByLastRaceSpeed()


def _train_row(
    race_id: int, horse_id: int, speed: float, last_race_speed: float
) -> dict[str, object]:
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
        "LastRaceSpeed": last_race_speed,
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


def _horse_stat(horse_id: int, last_race_speed: float | None) -> dict[str, object]:
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


def _fitted_algo(max_horses: int = 5) -> _CharacterizationRegressor:
    algo = _CharacterizationRegressor(max_horses=max_horses)
    rows = [
        _train_row(
            race_id=r, horse_id=r * 10 + h, speed=14.0 + h, last_race_speed=14.0 + h
        )
        for r in range(1, 6)
        for h in range(3)
    ]
    algo.fit(_rd(pd.DataFrame(rows)))
    return algo


def test_regressor_top1_picks_are_pinned() -> None:
    algo = _fitted_algo(max_horses=5)

    # Race 10: complete, LastRaceSpeed 15<16<17 -> horse 103 wins.
    # Race 20: horse 202 has NaN LastRaceSpeed (required) -> whole race dropped.
    # Race 30: 6 runners > max_horses(5) -> dropped.
    races = pd.DataFrame(
        [_race_row(10, h, h) for h in (101, 102, 103)]
        + [_race_row(20, h, h) for h in (201, 202, 203)]
        + [_race_row(30, h, h) for h in range(301, 307)]
    )
    horse_stats = pd.DataFrame(
        [_horse_stat(101, 15.0), _horse_stat(102, 16.0), _horse_stat(103, 17.0)]
        + [_horse_stat(201, 15.0), _horse_stat(202, None), _horse_stat(203, 17.0)]
        + [_horse_stat(h, 15.0) for h in range(301, 307)]
    )
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in races["HorseId"]])

    result = algo.predict(_serve(races, horse_stats, jockey_stats))

    assert list(result.columns) == ["RaceId", "HorseId"]
    assert result.to_records(index=False).tolist() == [(10, 103)]


def test_regressor_full_field_winner_per_complete_race() -> None:
    algo = _fitted_algo(max_horses=10)
    races = pd.DataFrame(
        [_race_row(10, h, h) for h in (101, 102, 103)]
        + [_race_row(20, h, h) for h in (201, 202, 203)]
    )
    horse_stats = pd.DataFrame(
        [
            _horse_stat(101, 15.0),
            _horse_stat(102, 16.0),
            _horse_stat(103, 17.0),
            _horse_stat(201, 19.0),
            _horse_stat(202, 18.0),
            _horse_stat(203, 17.0),
        ]
    )
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in races["HorseId"]])

    result = algo.predict(_serve(races, horse_stats, jockey_stats))

    assert sorted(result.to_records(index=False).tolist()) == [(10, 103), (20, 201)]
