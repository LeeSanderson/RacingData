from datetime import datetime

import pandas as pd

from race_analytics.algorithms.xgboost_algorithm import XGBoostAlgorithm
from race_analytics.algorithms.ridge_regression import RidgeRegressionAlgorithm
from race_analytics.algorithms.ratings_xgboost import RatingsXGBoostUngatedAlgorithm
from race_analytics.algorithms.proxy_tsr_xgboost import ProxyTSRXGBoostAlgorithm
from race_analytics.algorithms.base import OPTIONAL_PREDICTORS

_LONG_AGO = datetime(2020, 1, 1)
_D1 = datetime(2021, 1, 1)


def _train_row(
    race_id, horse_id, wins=0, speed=16.0, tsr=90.0,
    last3_avspd=14.0, last3_trend=0.1, last3_relpos=0.5,
):
    return {
        "HorseId": horse_id, "RaceId": race_id, "Off": _D1,
        "CourseName": "Newmarket",
        "Wins": wins, "Speed": speed,
        "FinishingPosition": 2, "OverallBeatenDistance": 2.0,
        "HorseCount": 3, "TopSpeedRating": tsr,
        "LastRaceOfficialRating": 70.0, "LastRaceRacingPostRating": 95.0,
        "LastRaceTopSpeedRating": 92.0,
        "Last3RaceAvgSpeed": last3_avspd,
        "Last3RaceSpeedTrend": last3_trend,
        "Last3AvgRelFinishingPosition": last3_relpos,
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
        "WeightChange": 2.0, "DistanceChange": 0.0,
        "SurfaceSwitch": 0.0, "CodeSwitch": 0.0,
        # Tier-1 new optional predictors
        "RaceClass": 3.0, "Age": 4.0, "RelAge": 0.0,
        "DrawPct": 0.5, "RelDraw": 0.0, "IsHandicap": 1.0,
        "Pattern_Group1": 0.0, "Pattern_Group2": 0.0, "Pattern_Group3": 0.0,
        "Pattern_Listed": 0.0, "Pattern_None": 1.0,
        "AgeBand_2yo": 0.0, "AgeBand_3yo": 0.0, "AgeBand_3yoPlus": 0.0,
        "AgeBand_4yoPlus": 1.0, "AgeBand_None": 0.0,
        "SexRestriction_F": 0.0, "SexRestriction_FM": 0.0, "SexRestriction_Open": 1.0,
    }


def _make_train_df(n_races=5, horses_per_race=3):
    rows = [
        _train_row(r, r * 10 + h, wins=1 if h == 0 else 0)
        for r in range(1, n_races + 1)
        for h in range(horses_per_race)
    ]
    # One extra race with NaN Last3*: verifies algo tolerates them during fit.
    extra = n_races + 1
    for h in range(horses_per_race):
        rows.append(_train_row(
            extra, extra * 10 + h, wins=1 if h == 0 else 0,
            last3_avspd=None, last3_trend=None, last3_relpos=None,
        ))
    return pd.DataFrame(rows)


def _race_row(race_id, horse_id, jockey_id):
    return {
        "RaceId": race_id, "HorseId": horse_id, "JockeyId": jockey_id,
        "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
        "DistanceInMeters": 1600.0, "WeightInPounds": 126.0,
    }


def _horse_stat(horse_id, last3_avspd=14.0, last3_trend=0.1, last3_relpos=0.5):
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
        "Last3RaceAvgSpeed": last3_avspd,
        "Last3RaceSpeedTrend": last3_trend,
        "Last3AvgRelFinishingPosition": last3_relpos,
    }


def _jockey_stat(jockey_id):
    return {
        "JockeyId": jockey_id, "LastOff": _LONG_AGO,
        "JockeyNumberOfPriorRaces": 10.0,
        "JockeyWinPercentage": 0.2, "JockeyTop3Percentage": 0.5,
        "JockeyAvgRelFinishingPosition": 0.4,
    }


def _make_predict_fixtures(n_horses=3):
    races = pd.DataFrame([_race_row(99, h, h) for h in range(n_horses)])
    horse_stats = pd.DataFrame([
        _horse_stat(0),
        _horse_stat(1, last3_avspd=None, last3_trend=None, last3_relpos=None),
        _horse_stat(2),
    ])
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in range(n_horses)])
    return races, horse_stats, jockey_stats


# ── Test 1: XGBoostAlgorithm._fitted_predictors includes all Last3* after fit ──

def test_xgboost_fitted_predictors_include_last3_columns():
    algo = XGBoostAlgorithm()
    algo.fit(_make_train_df())
    for col in OPTIONAL_PREDICTORS:
        assert col in algo._fitted_predictors, f"{col} missing from _fitted_predictors"


# ── Test 2: XGBoostAlgorithm.predict returns non-empty with NaN Last3* horse ──

def test_xgboost_predict_tolerates_nan_last3_in_one_horse():
    algo = XGBoostAlgorithm()
    algo.fit(_make_train_df())
    races, horse_stats, jockey_stats = _make_predict_fixtures()
    result = algo.predict(races, horse_stats, jockey_stats)
    assert len(result) > 0


# ── Test 3: RidgeRegressionAlgorithm._fitted_predictors excludes all Last3* ───

def test_ridge_fitted_predictors_exclude_last3_columns():
    algo = RidgeRegressionAlgorithm()
    algo.fit(_make_train_df())
    for col in OPTIONAL_PREDICTORS:
        assert col not in algo._fitted_predictors, f"{col} should not be in Ridge _fitted_predictors"


# ── Test 4: RatingsXGBoostUngated predict returns non-empty with NaN Last3* ───

def test_ratings_xgboost_ungated_predict_tolerates_nan_last3_in_one_horse():
    algo = RatingsXGBoostUngatedAlgorithm()
    algo.fit(_make_train_df())
    races, horse_stats, jockey_stats = _make_predict_fixtures()
    result = algo.predict(races, horse_stats, jockey_stats)
    assert len(result) > 0


# ── Test 5: ProxyTSRXGBoost predict returns non-empty with NaN Last3* horse ──

def test_proxy_tsr_xgboost_predict_tolerates_nan_last3_in_one_horse():
    algo = ProxyTSRXGBoostAlgorithm()
    algo.fit(_make_train_df())
    races, horse_stats, jockey_stats = _make_predict_fixtures()
    result = algo.predict(races, horse_stats, jockey_stats)
    assert len(result) > 0
