from datetime import datetime

import pandas as pd

from race_analytics.algorithms import (
    GatedRankingClassifier as AbstainWrapperLTRAlgorithm,
)
from race_analytics.algorithms.ranking_classifier import (
    RankingClassifier as LTRProxyTSRAlgorithm,
)
from race_analytics.features.race_data import RaceDataBuilder

_LONG_AGO = datetime(2020, 1, 1)
D1 = datetime(2021, 1, 1)
_AS_OF = datetime(2026, 1, 1)


def _rd(df):
    return RaceDataBuilder().wrap_training(df)


def _serve(races, horse_stats, jockey_stats):
    return RaceDataBuilder().build_serving_from_stats(
        races, horse_stats, jockey_stats, None, as_of=_AS_OF
    )


def _train_row(
    horse_id: int,
    race_id: int,
    off: datetime = D1,
    wins: int = 0,
    finishing_position: int = 2,
) -> dict:
    return {
        "HorseId": horse_id,
        "RaceId": race_id,
        "Off": off,
        "Wins": wins,
        "FinishingPosition": finishing_position,
        "CourseName": "Newmarket",
        "Speed": 16.0,
        "OverallBeatenDistance": 2.0,
        "HorseCount": 8,
        "OfficialRating": 80.0,
        "RacingPostRating": 100.0,
        "TopSpeedRating": 90.0,
        "LastRaceOfficialRating": 70.0,
        "LastRaceRacingPostRating": 95.0,
        "LastRaceTopSpeedRating": 92.0,
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
        "LastRaceSpeed": 15.5,
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


def _race_row(race_id: int, horse_id: int, jockey_id: int) -> dict:
    return {
        "RaceId": race_id,
        "HorseId": horse_id,
        "JockeyId": jockey_id,
        "Surface": "Turf",
        "Going": "Good",
        "RaceType": "Flat",
        "DistanceInMeters": 1600.0,
        "WeightInPounds": 126.0,
        "OfficialRating": 80.0,
        "RacingPostRating": 100.0,
        "TopSpeedRating": 90.0,
    }


def _horse_stat(horse_id: int) -> dict:
    return {
        "HorseId": horse_id,
        "LastOff": _LONG_AGO,
        "LastRaceDistanceInMeters": 1600.0,
        "LastRaceWeightInPounds": 126.0,
        "LastRaceAvgRelFinishingPosition": 0.5,
        "LastRaceSpeed": 16.0,
        "LastRaceOfficialRating": 70.0,
        "LastRaceRacingPostRating": 95.0,
        "LastRaceTopSpeedRating": 92.0,
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


def _jockey_stat(jockey_id: int) -> dict:
    return {
        "JockeyId": jockey_id,
        "LastOff": _LONG_AGO,
        "JockeyNumberOfPriorRaces": 10.0,
        "JockeyWinPercentage": 0.2,
        "JockeyTop3Percentage": 0.5,
        "JockeyAvgRelFinishingPosition": 0.4,
    }


def _make_train_df() -> pd.DataFrame:
    rows = [
        _train_row(
            horse_id=r * 10 + h,
            race_id=r,
            wins=1 if h == 0 else 0,
            finishing_position=h + 1,
        )
        for r in range(1, 6)
        for h in range(3)
    ]
    return pd.DataFrame(rows)


def test_ltr_fit_and_predict_field_returns_required_columns():
    algo = LTRProxyTSRAlgorithm(max_horses=10)
    algo.fit(_rd(_make_train_df()))

    races = pd.DataFrame([_race_row(10, h, h) for h in [101, 102, 103]])
    horse_stats = pd.DataFrame([_horse_stat(h) for h in [101, 102, 103]])
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in [101, 102, 103]])

    result = algo.predict_field(_serve(races, horse_stats, jockey_stats))

    assert not result.empty
    for col in ["RaceId", "HorseId", "WinProbability", "PredictedRank"]:
        assert col in result.columns, f"missing column: {col}"


def test_gated_ranking_classifier_uses_gap_metric():
    algo = AbstainWrapperLTRAlgorithm(max_horses=10)
    assert algo.get_confidence_gate().metric == "gap"


def test_ltr_and_abstain_registered_in_algorithms():
    from race_analytics.algorithms import ALGORITHMS

    names = [type(a).__name__ for a in ALGORITHMS]
    assert "RankingClassifier" in names
    assert "GatedRankingClassifier" in names
