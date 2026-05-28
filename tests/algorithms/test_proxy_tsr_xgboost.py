import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from race_analytics.algorithms.proxy_tsr_xgboost import ProxyTSRXGBoostAlgorithm

_LONG_AGO = datetime(2020, 1, 1)
D1 = datetime(2021, 1, 1)
D2 = datetime(2021, 2, 1)
D3 = datetime(2021, 3, 1)


def _train_row(horse_id: int, race_id: int, off: datetime = D1, wins: int = 0,
               tsr: float | None = 90.0) -> dict:
    return {
        "HorseId": horse_id, "RaceId": race_id, "Off": off,
        "Wins": wins,
        "CourseName": "Newmarket",
        "Speed": 16.0, "FinishingPosition": 2, "OverallBeatenDistance": 2.0,
        "HorseCount": 8,
        "OfficialRating": 80.0, "RacingPostRating": 100.0, "TopSpeedRating": tsr,
        "DistanceInMeters": 1600.0, "WeightInPounds": 126.0,
        "Surface_AllWeather": 0.0, "Surface_Dirt": 0.0, "Surface_Turf": 1.0,
        "Going_Firm": 0.0, "Going_Good": 1.0, "Going_Good_To_Firm": 0.0,
        "Going_Good_To_Soft": 0.0, "Going_Heavy": 0.0, "Going_Soft": 0.0,
        "RaceType_Flat": 1.0, "RaceType_Hurdle": 0.0,
        "RaceType_Other": 0.0, "RaceType_SteepleChase": 0.0,
        "LastRaceDistanceInMeters": 1600.0, "LastRaceWeightInPounds": 126.0,
        "LastRaceSpeed": 15.5, "DaysRested": 7.0,
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


def _race_row(race_id: int, horse_id: int, jockey_id: int,
              tsr: float | None = 90.0) -> dict:
    return {
        "RaceId": race_id, "HorseId": horse_id, "JockeyId": jockey_id,
        "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
        "DistanceInMeters": 1600.0, "WeightInPounds": 126.0,
        "OfficialRating": 80.0, "RacingPostRating": 100.0, "TopSpeedRating": tsr,
    }


def _horse_stat(horse_id: int) -> dict:
    return {
        "HorseId": horse_id, "LastOff": _LONG_AGO,
        "LastRaceDistanceInMeters": 1600.0, "LastRaceWeightInPounds": 126.0,
        "LastRaceAvgRelFinishingPosition": 0.5, "LastRaceSpeed": 16.0,
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


def _make_train_df() -> pd.DataFrame:
    """Three races, three horses each, enough labelled rows for ProxyTSRModel."""
    rows = [
        _train_row(horse_id=r * 10 + h, race_id=r, off=D1, wins=1 if h == 0 else 0,
                   tsr=90.0 + h)
        for r in range(1, 6) for h in range(3)
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def trained_algo() -> ProxyTSRXGBoostAlgorithm:
    algo = ProxyTSRXGBoostAlgorithm(max_horses=10)
    algo.fit(_make_train_df())
    return algo


# ── 1. fit completes ──────────────────────────────────────────────────────────


def test_fit_completes_without_error():
    algo = ProxyTSRXGBoostAlgorithm(max_horses=10)
    algo.fit(_make_train_df())  # must not raise


# ── 2. predict returns correct columns ───────────────────────────────────────


def test_predict_returns_raceId_and_horseId_columns(trained_algo):
    races = pd.DataFrame([_race_row(10, h, h) for h in [101, 102, 103]])
    horse_stats = pd.DataFrame([_horse_stat(h) for h in [101, 102, 103]])
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in [101, 102, 103]])

    result = trained_algo.predict(races, horse_stats, jockey_stats)

    assert list(result.columns) == ["RaceId", "HorseId"]


# ── 3. predict returns one row per race ───────────────────────────────────────


def test_predict_returns_one_row_per_race(trained_algo):
    races = pd.DataFrame(
        [_race_row(10, h, h) for h in [101, 102, 103]]
        + [_race_row(20, h, h) for h in [201, 202, 203]]
    )
    horse_stats = pd.DataFrame([_horse_stat(h) for h in [101, 102, 103, 201, 202, 203]])
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in [101, 102, 103, 201, 202, 203]])

    result = trained_algo.predict(races, horse_stats, jockey_stats)

    assert len(result) == 2
    assert set(result["RaceId"]) == {10, 20}
    assert result["RaceId"].nunique() == len(result)


# ── 4. No TSR gating — predicts on races with no real TopSpeedRating ──────────


def test_predict_includes_races_with_no_real_tsr(trained_algo):
    # Race 10: horses with real TSR; Race 20: all TSR = NaN
    races = pd.DataFrame(
        [_race_row(10, h, h, tsr=90.0) for h in [101, 102, 103]]
        + [_race_row(20, h, h, tsr=None) for h in [201, 202, 203]]
    )
    horse_stats = pd.DataFrame([_horse_stat(h) for h in [101, 102, 103, 201, 202, 203]])
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in [101, 102, 103, 201, 202, 203]])

    result = trained_algo.predict(races, horse_stats, jockey_stats)

    # Both races should be predicted — no TSR gate
    assert 20 in result["RaceId"].values


# ── 5. Algorithm is registered in the ALGORITHMS list ────────────────────────


def test_algorithm_is_registered():
    from race_analytics.algorithms import ALGORITHMS
    algo_types = [type(a).__name__ for a in ALGORITHMS]
    assert "ProxyTSRXGBoostAlgorithm" in algo_types
