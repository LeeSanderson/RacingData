import numpy as np
import pandas as pd
import pytest
from datetime import datetime

from race_analytics.algorithms.recency_weighted_win_classifier import RecencyWeightedWinClassifier as RecencyWeightedProxyTSRAlgorithm
from race_analytics.features.race_data import RaceData

_LONG_AGO = datetime(2020, 1, 1)
D_OLD = datetime(2021, 1, 1)
D_NEW = datetime(2021, 5, 1)


def _train_row(horse_id: int, race_id: int, off: datetime = D_OLD,
               wins: int = 0, finishing_position: int = 2) -> dict:
    return {
        "HorseId": horse_id, "RaceId": race_id, "Off": off,
        "Wins": wins, "FinishingPosition": finishing_position,
        "CourseName": "Newmarket",
        "Speed": 16.0, "OverallBeatenDistance": 2.0, "HorseCount": 8,
        "OfficialRating": 80.0, "RacingPostRating": 100.0, "TopSpeedRating": 90.0,
        "LastRaceOfficialRating": 70.0, "LastRaceRacingPostRating": 95.0,
        "LastRaceTopSpeedRating": 92.0,
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


def _race_row(race_id: int, horse_id: int, jockey_id: int) -> dict:
    return {
        "RaceId": race_id, "HorseId": horse_id, "JockeyId": jockey_id,
        "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
        "DistanceInMeters": 1600.0, "WeightInPounds": 126.0,
        "OfficialRating": 80.0, "RacingPostRating": 100.0, "TopSpeedRating": 90.0,
    }


def _horse_stat(horse_id: int) -> dict:
    return {
        "HorseId": horse_id, "LastOff": _LONG_AGO,
        "LastRaceDistanceInMeters": 1600.0, "LastRaceWeightInPounds": 126.0,
        "LastRaceAvgRelFinishingPosition": 0.5, "LastRaceSpeed": 16.0,
        "LastRaceOfficialRating": 70.0, "LastRaceRacingPostRating": 95.0,
        "LastRaceTopSpeedRating": 92.0,
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


def _make_train_df_varied_dates() -> pd.DataFrame:
    """Five races: first two on D_OLD, last two on D_NEW, one on a mid date."""
    rows = []
    dates = [D_OLD, D_OLD, datetime(2021, 3, 1), D_NEW, D_NEW]
    for i, off in enumerate(dates):
        race_id = i + 1
        for h in range(3):
            rows.append(_train_row(
                horse_id=race_id * 10 + h,
                race_id=race_id,
                off=off,
                wins=1 if h == 0 else 0,
                finishing_position=h + 1,
            ))
    return pd.DataFrame(rows)


def test_recency_and_abstain_registered_in_algorithms():
    from race_analytics.algorithms import ALGORITHMS
    names = [type(a).__name__ for a in ALGORITHMS]
    assert "RecencyWeightedWinClassifier" in names
    assert "GatedRecencyWeightedWinClassifier" in names


def _prepared_weights(algo: RecencyWeightedProxyTSRAlgorithm, train_df: pd.DataFrame,
                      as_of: pd.Timestamp) -> pd.DataFrame:
    """Run the training-prep hook and return the prepared frame carrying `_w`."""
    return algo._prepare_training(RaceData(train_df.copy(), as_of)).frame


def test_decay_weights_older_races_lower():
    algo = RecencyWeightedProxyTSRAlgorithm(max_horses=10)
    train_df = _make_train_df_varied_dates()
    as_of = pd.to_datetime(train_df["Off"]).max().normalize() + pd.Timedelta(days=1)

    w = _prepared_weights(algo, train_df, as_of)
    off = pd.to_datetime(w["Off"]).dt.date
    assert w.loc[off == D_OLD.date(), "_w"].mean() < w.loc[off == D_NEW.date(), "_w"].mean()


def test_decay_weights_derive_from_as_of_not_wall_clock():
    """Identical rows under two different `as_of` dates yield different weights, and a
    later `as_of` (every race relatively older) yields uniformly smaller weights."""
    train_df = _make_train_df_varied_dates()
    early = _prepared_weights(RecencyWeightedProxyTSRAlgorithm(), train_df, pd.Timestamp("2021-05-02"))
    late = _prepared_weights(RecencyWeightedProxyTSRAlgorithm(), train_df, pd.Timestamp("2021-08-02"))

    assert not np.allclose(early["_w"].to_numpy(), late["_w"].to_numpy())
    assert (late["_w"].to_numpy() <= early["_w"].to_numpy() + 1e-12).all()


def test_recency_weighted_fit_and_predict_field_smoke():
    algo = RecencyWeightedProxyTSRAlgorithm(max_horses=10)
    algo.fit(_make_train_df_varied_dates())

    races = pd.DataFrame([_race_row(10, h, h) for h in [101, 102, 103]])
    horse_stats = pd.DataFrame([_horse_stat(h) for h in [101, 102, 103]])
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in [101, 102, 103]])

    result = algo.predict_field(races, horse_stats, jockey_stats)

    assert not result.empty
    for col in ["RaceId", "HorseId", "WinProbability", "PredictedRank"]:
        assert col in result.columns, f"missing column: {col}"
