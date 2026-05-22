import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import pytest

from scripts.evaluate import _extract_known_races, _compute_horse_stats, _compute_jockey_stats


# ================================================================
# _extract_known_races
# ================================================================

def test_extract_known_races_removes_unknown_races():
    df = pd.DataFrame([
        {"RaceId": 1, "HorseId": 10, "KnownHorseAndJockey": True},
        {"RaceId": 1, "HorseId": 11, "KnownHorseAndJockey": True},
        {"RaceId": 2, "HorseId": 20, "KnownHorseAndJockey": False},
        {"RaceId": 2, "HorseId": 21, "KnownHorseAndJockey": False},
    ])
    result = _extract_known_races(df)
    assert set(result["RaceId"]) == {1}
    assert len(result) == 2


def test_extract_known_races_keeps_all_when_all_known():
    df = pd.DataFrame([
        {"RaceId": 1, "HorseId": 10, "KnownHorseAndJockey": True},
        {"RaceId": 2, "HorseId": 20, "KnownHorseAndJockey": True},
    ])
    result = _extract_known_races(df)
    assert len(result) == 2


def test_extract_known_races_returns_empty_when_none_known():
    df = pd.DataFrame([
        {"RaceId": 1, "HorseId": 10, "KnownHorseAndJockey": False},
    ])
    assert _extract_known_races(df).empty


# ================================================================
# Shared fixture helpers
# ================================================================

def _train_row(horse_id, jockey_id, off, finishing_pos=2, horse_count=5,
               speed=15.0, dist=1600.0, weight=126.0,
               n_prior=3.0, last_avg_rel_pos=0.3,
               j_n_prior=5.0, j_win_pct=0.2, j_top3_pct=0.4, j_avg_rel=0.35):
    return {
        "HorseId": horse_id, "JockeyId": jockey_id,
        "Off": pd.Timestamp(off),
        "FinishingPosition": finishing_pos, "HorseCount": horse_count,
        "Speed": speed, "DistanceInMeters": dist, "WeightInPounds": weight,
        "NumberOfPriorRaces": n_prior,
        "LastRaceAvgRelFinishingPosition": last_avg_rel_pos,
        "JockeyNumberOfPriorRaces": j_n_prior,
        "JockeyWinPercentage": j_win_pct,
        "JockeyTop3Percentage": j_top3_pct,
        "JockeyAvgRelFinishingPosition": j_avg_rel,
        "Surface_AllWeather": 0.0, "Surface_Dirt": 0.0, "Surface_Turf": 1.0,
        "Going_Good": 1.0, "Going_Good_To_Soft": 0.0, "Going_Soft": 0.0,
        "Going_Good_To_Firm": 0.0, "Going_Firm": 0.0, "Going_Heavy": 0.0,
        "RaceType_Flat": 1.0, "RaceType_Hurdle": 0.0,
        "RaceType_Other": 0.0, "RaceType_SteepleChase": 0.0,
    }


# ================================================================
# _compute_horse_stats
# ================================================================

def test_horse_stats_one_row_per_horse():
    rows = [
        _train_row(horse_id=1, jockey_id=10, off="2026-01-01"),
        _train_row(horse_id=1, jockey_id=10, off="2026-02-01"),
        _train_row(horse_id=2, jockey_id=20, off="2026-01-15"),
    ]
    result = _compute_horse_stats(pd.DataFrame(rows))
    assert len(result) == 2
    assert set(result["HorseId"]) == {1, 2}


def test_horse_stats_uses_most_recent_race_as_last_off():
    rows = [
        _train_row(horse_id=1, jockey_id=10, off="2026-01-01", speed=14.0),
        _train_row(horse_id=1, jockey_id=10, off="2026-03-01", speed=16.0),
    ]
    result = _compute_horse_stats(pd.DataFrame(rows))
    row = result[result["HorseId"] == 1].iloc[0]
    assert row["LastOff"] == pd.Timestamp("2026-03-01")
    assert row["LastRaceSpeed"] == pytest.approx(16.0)


def test_horse_stats_has_required_columns():
    rows = [_train_row(horse_id=1, jockey_id=10, off="2026-01-01")]
    result = _compute_horse_stats(pd.DataFrame(rows))
    for col in [
        "HorseId", "LastOff", "LastRaceDistanceInMeters",
        "LastRaceWeightInPounds", "LastRaceSpeed",
        "LastRaceAvgRelFinishingPosition",
        "LastRaceSurface_Turf", "LastRaceGoing_Good", "LastRaceRaceType_Flat",
    ]:
        assert col in result.columns, f"Missing column: {col}"


def test_horse_stats_avg_rel_pos_incorporates_last_race():
    # n_prior=4, last_avg_rel_pos=0.4, finishing_pos=1, horse_count=5
    # updated = (0.4*4 + 1/5) / 5 = (1.6+0.2)/5 = 0.36
    rows = [_train_row(
        horse_id=1, jockey_id=10, off="2026-01-01",
        finishing_pos=1, horse_count=5,
        n_prior=4.0, last_avg_rel_pos=0.4,
    )]
    result = _compute_horse_stats(pd.DataFrame(rows))
    assert result.iloc[0]["LastRaceAvgRelFinishingPosition"] == pytest.approx(0.36)


# ================================================================
# _compute_jockey_stats
# ================================================================

def test_jockey_stats_one_row_per_jockey():
    rows = [
        _train_row(horse_id=1, jockey_id=10, off="2026-01-01"),
        _train_row(horse_id=2, jockey_id=10, off="2026-02-01"),
        _train_row(horse_id=3, jockey_id=20, off="2026-01-15"),
    ]
    result = _compute_jockey_stats(pd.DataFrame(rows))
    assert len(result) == 2
    assert set(result["JockeyId"]) == {10, 20}


def test_jockey_stats_has_required_columns():
    rows = [_train_row(horse_id=1, jockey_id=10, off="2026-01-01")]
    result = _compute_jockey_stats(pd.DataFrame(rows))
    for col in [
        "JockeyId", "LastOff", "JockeyNumberOfPriorRaces",
        "JockeyWinPercentage", "JockeyTop3Percentage",
        "JockeyAvgRelFinishingPosition",
    ]:
        assert col in result.columns, f"Missing column: {col}"


def test_jockey_stats_excludes_jockey_id_zero():
    rows = [
        _train_row(horse_id=1, jockey_id=0, off="2026-01-01"),
        _train_row(horse_id=2, jockey_id=10, off="2026-01-01"),
    ]
    result = _compute_jockey_stats(pd.DataFrame(rows))
    assert 0 not in result["JockeyId"].values
    assert len(result) == 1


def test_jockey_stats_uses_most_recent_race_as_last_off():
    rows = [
        _train_row(horse_id=1, jockey_id=10, off="2026-01-01"),
        _train_row(horse_id=2, jockey_id=10, off="2026-03-01"),
    ]
    result = _compute_jockey_stats(pd.DataFrame(rows))
    assert result[result["JockeyId"] == 10].iloc[0]["LastOff"] == pd.Timestamp("2026-03-01")
