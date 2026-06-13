import pytest
import pandas as pd
from datetime import datetime

from race_analytics.algorithms.ratings_xgboost import (
    RatingsXGBoostAlgorithm,
    RatingsXGBoostUngatedAlgorithm,
)
from race_analytics.features.race_data import RaceDataBuilder

_LONG_AGO = datetime(2020, 1, 1)
D1 = datetime(2021, 1, 1)
_AS_OF = datetime(2026, 1, 1)


def _train():
    return RaceDataBuilder().wrap_training(_make_train_df())


def _serve(races, horse_stats, jockey_stats):
    return RaceDataBuilder().build_serving_from_stats(
        races, horse_stats, jockey_stats, None, as_of=_AS_OF
    )

_CURRENT_RATINGS = ["OfficialRating", "RacingPostRating", "TopSpeedRating"]
_LASTRACE_RATINGS = [
    "LastRaceOfficialRating",
    "LastRaceRacingPostRating",
    "LastRaceTopSpeedRating",
]


def _train_row(horse_id: int, race_id: int, wins: int = 0,
               last_tsr: float | None = 90.0) -> dict:
    """A training row carrying BOTH current-race ratings and the previous-race
    LastRace* ratings, so a test can prove the current-race ones are dropped."""
    return {
        "HorseId": horse_id, "RaceId": race_id, "Off": D1, "Wins": wins,
        "Speed": 16.0, "HorseCount": 3,
        # current-race (post-race) ratings — must NOT be used as features
        "OfficialRating": 80.0, "RacingPostRating": 100.0, "TopSpeedRating": 88.0,
        # previous-race ratings — the leak-free signal the model should use
        "LastRaceOfficialRating": 70.0, "LastRaceRacingPostRating": 95.0,
        "LastRaceTopSpeedRating": last_tsr,
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
    """A race card row with NO rating columns — ratings must come from horse_stats."""
    return {
        "RaceId": race_id, "HorseId": horse_id, "JockeyId": jockey_id,
        "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
        "DistanceInMeters": 1600.0, "WeightInPounds": 126.0,
    }


def _horse_stat(horse_id: int, last_tsr: float | None = 90.0) -> dict:
    return {
        "HorseId": horse_id, "LastOff": _LONG_AGO,
        "LastRaceDistanceInMeters": 1600.0, "LastRaceWeightInPounds": 126.0,
        "LastRaceAvgRelFinishingPosition": 0.5, "LastRaceSpeed": 16.0,
        "LastRaceOfficialRating": 70.0, "LastRaceRacingPostRating": 95.0,
        "LastRaceTopSpeedRating": last_tsr,
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
    rows = [
        _train_row(horse_id=r * 10 + h, race_id=r, wins=1 if h == 0 else 0,
                   last_tsr=90.0 + h)
        for r in range(1, 6) for h in range(3)
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def trained_algo() -> RatingsXGBoostAlgorithm:
    algo = RatingsXGBoostAlgorithm(max_horses=10)
    algo.fit(_train())
    return algo


# ── fit() uses previous-race ratings, never current-race ratings ──────────────


def test_fit_uses_lastrace_ratings_and_excludes_current_race_ratings():
    algo = RatingsXGBoostAlgorithm(max_horses=10)
    algo.fit(_train())
    feats = algo._feature_cols
    for col in _LASTRACE_RATINGS:
        assert col in feats, f"missing previous-race rating feature: {col}"
        assert f"Rel{col}" in feats, f"missing relative previous-race feature: Rel{col}"
    for col in _CURRENT_RATINGS:
        assert col not in feats, f"current-race rating leaked into features: {col}"
        assert f"Rel{col}" not in feats, f"current-race relative leaked in: Rel{col}"


# ── require_tsr gate is defined on LastRaceTopSpeedRating coverage ─────────────


def test_gate_filters_on_lastrace_tsr_coverage():
    gated = RatingsXGBoostAlgorithm(max_horses=10)
    gated.fit(_train())
    ungated = RatingsXGBoostUngatedAlgorithm(max_horses=10)
    ungated.fit(_train())

    races = pd.DataFrame(
        [_race_row(10, h, h) for h in [101, 102, 103]]
        + [_race_row(20, h, h) for h in [201, 202, 203]]
    )
    # Race 10: every horse has a LastRaceTopSpeedRating.
    # Race 20: horse 201 has none -> gated must drop the whole race.
    horse_stats = pd.DataFrame(
        [_horse_stat(h) for h in [101, 102, 103]]
        + [_horse_stat(201, last_tsr=None), _horse_stat(202), _horse_stat(203)]
    )
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in [101, 102, 103, 201, 202, 203]])

    gated_res = gated.predict(_serve(races, horse_stats, jockey_stats))
    ungated_res = ungated.predict(_serve(races, horse_stats, jockey_stats))

    assert 10 in gated_res["RaceId"].values
    assert 20 not in gated_res["RaceId"].values
    assert 20 in ungated_res["RaceId"].values


# ── predict() sources ratings from horse_stats, not the race card ─────────────


def test_predict_works_from_card_without_rating_columns(trained_algo):
    races = pd.DataFrame([_race_row(10, h, h) for h in [101, 102, 103]])
    assert not any(c in races.columns for c in _CURRENT_RATINGS), (
        "card fixture should carry no rating columns"
    )
    horse_stats = pd.DataFrame([_horse_stat(h) for h in [101, 102, 103]])
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in [101, 102, 103]])

    result = trained_algo.predict(_serve(races, horse_stats, jockey_stats))

    assert list(result.columns) == ["RaceId", "HorseId"]
    assert result["RaceId"].tolist() == [10]


# ── both variants stay registered for comparison ─────────────────────────────


def test_both_variants_registered():
    from race_analytics.algorithms import ALGORITHMS
    names = [type(a).__name__ for a in ALGORITHMS]
    assert "RatingsXGBoostAlgorithm" in names
    assert "RatingsXGBoostUngatedAlgorithm" in names
