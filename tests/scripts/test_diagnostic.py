import numpy as np
import pandas as pd
import pytest

from race_analytics.scripts.diagnostic import (
    _distance_band,
    _field_size_band,
    _identify_picks,
    _roi,
    _segment_table,
)

# ================================================================
# _distance_band
# ================================================================


def test_distance_band_under_6f():
    assert _distance_band(5 * 201.168) == "<6f"


def test_distance_band_6_to_8f():
    assert _distance_band(7 * 201.168) == "6-8f"


def test_distance_band_8_to_10f():
    assert _distance_band(9 * 201.168) == "8-10f"


def test_distance_band_10_to_12f():
    assert _distance_band(11 * 201.168) == "10-12f"


def test_distance_band_12_to_16f():
    assert _distance_band(14 * 201.168) == "12-16f"


def test_distance_band_16f_plus():
    assert _distance_band(20 * 201.168) == "16f+"


def test_distance_band_na_returns_unknown():
    assert _distance_band(float("nan")) == "Unknown"


# ================================================================
# _field_size_band
# ================================================================


def test_field_size_band_small():
    assert _field_size_band(4) == "2-5"


def test_field_size_band_medium():
    assert _field_size_band(7) == "6-8"


def test_field_size_band_large():
    assert _field_size_band(10) == "9-12"


def test_field_size_band_very_large():
    assert _field_size_band(15) == "13-16"


def test_field_size_band_huge():
    assert _field_size_band(20) == "17+"


def test_field_size_band_boundaries():
    assert _field_size_band(5) == "2-5"
    assert _field_size_band(6) == "6-8"
    assert _field_size_band(8) == "6-8"
    assert _field_size_band(9) == "9-12"
    assert _field_size_band(12) == "9-12"
    assert _field_size_band(13) == "13-16"
    assert _field_size_band(16) == "13-16"
    assert _field_size_band(17) == "17+"


def test_field_size_band_na_returns_unknown():
    assert _field_size_band(float("nan")) == "Unknown"


# ================================================================
# _identify_picks
# ================================================================


def _race_df(rows):
    """Helper to build a minimal eval-CSV-shaped DataFrame."""
    return pd.DataFrame(rows)


def test_identify_picks_single_horse_per_race():
    df = _race_df(
        [
            {
                "FoldDate": "2026-01-01",
                "Algorithm": "Algo",
                "RaceId": 1,
                "HorseId": 10,
                "WinProbability": 0.3,
                "PredictedScore": np.nan,
            },
        ]
    )
    result = _identify_picks(df)
    assert len(result) == 1
    assert result.iloc[0]["HorseId"] == 10


def test_identify_picks_selects_highest_win_probability():
    df = _race_df(
        [
            {
                "FoldDate": "2026-01-01",
                "Algorithm": "Algo",
                "RaceId": 1,
                "HorseId": 10,
                "WinProbability": 0.20,
                "PredictedScore": np.nan,
            },
            {
                "FoldDate": "2026-01-01",
                "Algorithm": "Algo",
                "RaceId": 1,
                "HorseId": 11,
                "WinProbability": 0.45,
                "PredictedScore": np.nan,
            },
            {
                "FoldDate": "2026-01-01",
                "Algorithm": "Algo",
                "RaceId": 1,
                "HorseId": 12,
                "WinProbability": 0.15,
                "PredictedScore": np.nan,
            },
        ]
    )
    result = _identify_picks(df)
    assert len(result) == 1
    assert result.iloc[0]["HorseId"] == 11


def test_identify_picks_falls_back_to_predicted_score_when_no_probability():
    df = _race_df(
        [
            {
                "FoldDate": "2026-01-01",
                "Algorithm": "Algo",
                "RaceId": 1,
                "HorseId": 10,
                "WinProbability": np.nan,
                "PredictedScore": 14.0,
            },
            {
                "FoldDate": "2026-01-01",
                "Algorithm": "Algo",
                "RaceId": 1,
                "HorseId": 11,
                "WinProbability": np.nan,
                "PredictedScore": 17.5,
            },
        ]
    )
    result = _identify_picks(df)
    assert len(result) == 1
    assert result.iloc[0]["HorseId"] == 11


def test_identify_picks_ignores_na_win_probability_rows_if_another_has_value():
    df = _race_df(
        [
            {
                "FoldDate": "2026-01-01",
                "Algorithm": "Algo",
                "RaceId": 1,
                "HorseId": 10,
                "WinProbability": np.nan,
                "PredictedScore": 99.0,
            },
            {
                "FoldDate": "2026-01-01",
                "Algorithm": "Algo",
                "RaceId": 1,
                "HorseId": 11,
                "WinProbability": 0.35,
                "PredictedScore": 1.0,
            },
        ]
    )
    result = _identify_picks(df)
    assert result.iloc[0]["HorseId"] == 11


def test_identify_picks_one_pick_per_algo_per_race_per_fold():
    df = _race_df(
        [
            {
                "FoldDate": "2026-01-01",
                "Algorithm": "A",
                "RaceId": 1,
                "HorseId": 10,
                "WinProbability": 0.4,
                "PredictedScore": np.nan,
            },
            {
                "FoldDate": "2026-01-01",
                "Algorithm": "B",
                "RaceId": 1,
                "HorseId": 10,
                "WinProbability": 0.2,
                "PredictedScore": np.nan,
            },
            {
                "FoldDate": "2026-01-01",
                "Algorithm": "B",
                "RaceId": 1,
                "HorseId": 11,
                "WinProbability": 0.5,
                "PredictedScore": np.nan,
            },
            {
                "FoldDate": "2026-01-02",
                "Algorithm": "A",
                "RaceId": 1,
                "HorseId": 20,
                "WinProbability": 0.3,
                "PredictedScore": np.nan,
            },
        ]
    )
    result = _identify_picks(df)
    assert len(result) == 3  # (A,1,01), (B,1,01), (A,1,02)


# ================================================================
# _roi
# ================================================================


def _picks_df(rows):
    return pd.DataFrame(rows)


def test_roi_empty_returns_zero():
    df = _picks_df([])
    assert _roi(df) == pytest.approx(0.0)


def test_roi_all_wins():
    df = _picks_df(
        [
            {"FinishingPosition": 1, "DecimalOdds": 3.0},
            {"FinishingPosition": 1, "DecimalOdds": 5.0},
        ]
    )
    # profit = (3-1) + (5-1) = 6; roi = 6/2 = 3.0
    assert _roi(df) == pytest.approx(3.0)


def test_roi_all_losses():
    df = _picks_df(
        [
            {"FinishingPosition": 2, "DecimalOdds": 3.0},
            {"FinishingPosition": 3, "DecimalOdds": 5.0},
        ]
    )
    # profit = -1 + -1 = -2; roi = -2/2 = -1.0
    assert _roi(df) == pytest.approx(-1.0)


def test_roi_mixed():
    df = _picks_df(
        [
            {"FinishingPosition": 1, "DecimalOdds": 4.0},
            {"FinishingPosition": 2, "DecimalOdds": 3.0},
            {"FinishingPosition": 3, "DecimalOdds": 6.0},
        ]
    )
    # profit = (4-1) + (-1) + (-1) = 1; roi = 1/3
    assert _roi(df) == pytest.approx(1 / 3)


# ================================================================
# _segment_table
# ================================================================


def _seg_picks():
    return pd.DataFrame(
        [
            {"FinishingPosition": 1, "DecimalOdds": 4.0, "RaceType": "Flat"},
            {"FinishingPosition": 2, "DecimalOdds": 3.0, "RaceType": "Flat"},
            {"FinishingPosition": 1, "DecimalOdds": 6.0, "RaceType": "Hurdle"},
            {"FinishingPosition": 3, "DecimalOdds": 5.0, "RaceType": "Hurdle"},
            {"FinishingPosition": 2, "DecimalOdds": 2.0, "RaceType": "Hurdle"},
        ]
    )


def test_segment_table_has_required_columns():
    result = _segment_table(_seg_picks(), "RaceType")
    assert list(result.columns) == ["RaceType", "Bets", "WinRate", "ROI", "Coverage"]


def test_segment_table_bets_count_per_segment():
    result = _segment_table(_seg_picks(), "RaceType")
    flat_row = result[result["RaceType"] == "Flat"].iloc[0]
    hurdle_row = result[result["RaceType"] == "Hurdle"].iloc[0]
    assert flat_row["Bets"] == 2
    assert hurdle_row["Bets"] == 3


def test_segment_table_win_rate_per_segment():
    result = _segment_table(_seg_picks(), "RaceType")
    flat_row = result[result["RaceType"] == "Flat"].iloc[0]
    hurdle_row = result[result["RaceType"] == "Hurdle"].iloc[0]
    assert flat_row["WinRate"] == pytest.approx(0.5)
    assert hurdle_row["WinRate"] == pytest.approx(1 / 3)


def test_segment_table_roi_per_segment():
    result = _segment_table(_seg_picks(), "RaceType")
    # Flat: profit = (4-1) + (-1) = 2; roi = 2/2 = 1.0
    flat_row = result[result["RaceType"] == "Flat"].iloc[0]
    assert flat_row["ROI"] == pytest.approx(1.0)
    # Hurdle: profit = (6-1) + (-1) + (-1) = 3; roi = 3/3 = 1.0
    hurdle_row = result[result["RaceType"] == "Hurdle"].iloc[0]
    assert hurdle_row["ROI"] == pytest.approx(1.0)


def test_segment_table_coverage_sums_to_one():
    result = _segment_table(_seg_picks(), "RaceType")
    assert result["Coverage"].sum() == pytest.approx(1.0)
