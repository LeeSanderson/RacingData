import os
import pathlib
from typing import Any, ClassVar

import pandas as pd
import pytest

from race_analytics.features.race_data import RaceData
from race_analytics.scripts.predict import predict

# ================================================================
# Shared fake algorithms (FieldPredictor contract) and fixtures
# ================================================================


class _FakeAlgo:
    """FieldPredictor stub: one rank-1 pick per race with a fixed WinProbability."""

    max_horses = 99

    def __init__(self, max_horses: int = 99):
        self.max_horses = max_horses

    def fit(self, data: RaceData) -> None:
        pass

    def predict_field(self, data: RaceData) -> pd.DataFrame:
        frame = data.frame
        if frame.empty:
            return pd.DataFrame(
                columns=["RaceId", "HorseId", "WinProbability", "PredictedRank"]
            )
        out = (
            frame.groupby("RaceId").first().reset_index()[["RaceId", "HorseId"]].copy()
        )
        out["WinProbability"] = 0.5
        out["PredictedRank"] = 1.0
        return out

    def predict(self, data: RaceData) -> pd.DataFrame:
        return self.predict_field(data)[["RaceId", "HorseId"]]  # pyright: ignore[reportReturnType]  # column-list index yields DataFrame


def _write_race_features(path: str) -> None:
    pd.DataFrame(
        [
            {
                "RaceId": 1,
                "HorseId": 101,
                "Speed": 15.0,
                "DistanceInMeters": 1600.0,
                "WeightInPounds": 126.0,
            }
        ]
    ).to_csv(os.path.join(path, "Race_Features.csv"), index=False)


def _write_horse_stats(path: str) -> None:
    pd.DataFrame(
        [
            {"HorseId": 101, "LastOff": "2026-01-01 00:00:00"},
            {"HorseId": 201, "LastOff": "2026-01-01 00:00:00"},
            {"HorseId": 301, "LastOff": "2026-01-01 00:00:00"},
        ]
    ).to_csv(os.path.join(path, "Horse_Stats.csv"), index=False)


def _write_jockey_stats(path: str) -> None:
    pd.DataFrame(
        [
            {"JockeyId": 201, "LastOff": "2026-01-01 00:00:00"},
            {"JockeyId": 202, "LastOff": "2026-01-01 00:00:00"},
            {"JockeyId": 203, "LastOff": "2026-01-01 00:00:00"},
        ]
    ).to_csv(os.path.join(path, "Jockey_Stats.csv"), index=False)


def _write_trainer_stats(path: str) -> None:
    pd.DataFrame(
        [
            {
                "TrainerId": 301,
                "TrainerNumberOfPriorRaces": 5.0,
                "TrainerWinPercentage": 0.2,
                "TrainerTop3Percentage": 0.6,
                "TrainerAvgRelFinishingPosition": 0.4,
            }
        ]
    ).to_csv(os.path.join(path, "Trainer_Stats.csv"), index=False)


def _write_race_cards(path: str, rows: list[dict[str, Any]] | None = None) -> None:
    if rows is None:
        rows = [
            {
                "RaceId": 10,
                "HorseId": 101,
                "JockeyId": 201,
                "TrainerId": 301,
                "CourseId": 5,
                "CourseName": "Ascot",
                "Off": "05/21/2026 14:30:00",
                "HorseName": "Thunderbolt",
                "Surface": "Turf",
                "Going": "Good",
                "RaceType": "Flat",
                "DistanceInMeters": 1600.0,
                "WeightInPounds": 126.0,
            }
        ]
    pd.DataFrame(rows).to_csv(os.path.join(path, "TodaysRaceCards.csv"), index=False)


@pytest.fixture
def data_dir(tmp_path: pathlib.Path) -> str:
    _write_race_features(str(tmp_path))
    _write_horse_stats(str(tmp_path))
    _write_jockey_stats(str(tmp_path))
    _write_trainer_stats(str(tmp_path))
    _write_race_cards(str(tmp_path))
    return str(tmp_path)


# ================================================================
# test 1 — output file is created
# ================================================================


def test_predict_writes_todayspredictions_csv(data_dir: str) -> None:
    predict(data_path=data_dir, algorithm=_FakeAlgo())
    assert os.path.exists(os.path.join(data_dir, "TodaysPredictions.csv"))


# ================================================================
# test 2 — output has correct columns (predict_field carries WinProbability)
# ================================================================


def test_predict_output_has_correct_columns(data_dir: str) -> None:
    predict(data_path=data_dir, algorithm=_FakeAlgo())
    result = pd.read_csv(os.path.join(data_dir, "TodaysPredictions.csv"))
    assert list(result.columns) == [
        "RaceId",
        "CourseId",
        "CourseName",
        "Off",
        "HorseId",
        "HorseName",
        "WinProbability",
        "Stake",
    ]


# ================================================================
# test 3 — output is sorted by CourseName then Off
# ================================================================


def test_predict_output_is_sorted_by_coursename_off(tmp_path: pathlib.Path) -> None:
    rows = [
        {
            "RaceId": 10,
            "HorseId": 101,
            "JockeyId": 201,
            "TrainerId": 301,
            "CourseId": 5,
            "CourseName": "York",
            "Off": "05/21/2026 15:00:00",
            "HorseName": "Alpha",
            "Surface": "Turf",
            "Going": "Good",
            "RaceType": "Flat",
            "DistanceInMeters": 1600.0,
            "WeightInPounds": 126.0,
        },
        {
            "RaceId": 20,
            "HorseId": 201,
            "JockeyId": 202,
            "TrainerId": 301,
            "CourseId": 3,
            "CourseName": "Ascot",
            "Off": "05/21/2026 14:00:00",
            "HorseName": "Beta",
            "Surface": "Turf",
            "Going": "Good",
            "RaceType": "Flat",
            "DistanceInMeters": 1600.0,
            "WeightInPounds": 126.0,
        },
        {
            "RaceId": 30,
            "HorseId": 301,
            "JockeyId": 203,
            "TrainerId": 301,
            "CourseId": 3,
            "CourseName": "Ascot",
            "Off": "05/21/2026 13:00:00",
            "HorseName": "Gamma",
            "Surface": "Turf",
            "Going": "Good",
            "RaceType": "Flat",
            "DistanceInMeters": 1600.0,
            "WeightInPounds": 126.0,
        },
    ]
    _write_race_features(str(tmp_path))
    _write_horse_stats(str(tmp_path))
    _write_jockey_stats(str(tmp_path))
    _write_trainer_stats(str(tmp_path))
    _write_race_cards(str(tmp_path), rows=rows)

    predict(data_path=str(tmp_path), algorithm=_FakeAlgo())
    result = pd.read_csv(os.path.join(str(tmp_path), "TodaysPredictions.csv"))

    assert list(result["CourseName"]) == ["Ascot", "Ascot", "York"]
    assert list(result["HorseName"]) == ["Gamma", "Beta", "Alpha"]


# ================================================================
# test 4 — empty winners → empty CSV with correct columns
# ================================================================


class _EmptyAlgo:
    max_horses = 99

    def __init__(self, max_horses: int = 99):
        self.max_horses = max_horses

    def fit(self, data: RaceData) -> None:
        pass

    def predict_field(self, data: RaceData) -> pd.DataFrame:
        return pd.DataFrame(
            columns=["RaceId", "HorseId", "WinProbability", "PredictedRank"]
        )

    def predict(self, data: RaceData) -> pd.DataFrame:
        return pd.DataFrame(columns=["RaceId", "HorseId"])


def test_predict_empty_winners_writes_empty_csv(data_dir: str) -> None:
    predict(data_path=data_dir, algorithm=_EmptyAlgo())
    result = pd.read_csv(os.path.join(data_dir, "TodaysPredictions.csv"))
    assert list(result.columns) == [
        "RaceId",
        "CourseId",
        "CourseName",
        "Off",
        "HorseId",
        "HorseName",
        "WinProbability",
        "Stake",
    ]
    assert len(result) == 0


# ================================================================
# test 5 — trainer stats reach the serving RaceData (joined on TrainerId)
# ================================================================


class _ServeCapturingAlgo:
    """Captures the serving RaceData so tests can inspect what predict.py built."""

    max_horses = 99
    captured_frame: ClassVar[pd.DataFrame | None] = None

    def __init__(self, max_horses: int = 99):
        self.max_horses = max_horses

    def fit(self, data: RaceData) -> None:
        pass

    def predict_field(self, data: RaceData) -> pd.DataFrame:
        type(self).captured_frame = data.frame
        frame = data.frame
        if frame.empty:
            return pd.DataFrame(
                columns=["RaceId", "HorseId", "WinProbability", "PredictedRank"]
            )
        out = (
            frame.groupby("RaceId").first().reset_index()[["RaceId", "HorseId"]].copy()
        )
        out["WinProbability"] = 0.5
        out["PredictedRank"] = 1.0
        return out

    def predict(self, data: RaceData) -> pd.DataFrame:
        return self.predict_field(data)[["RaceId", "HorseId"]]  # pyright: ignore[reportReturnType]  # column-list index yields DataFrame


def test_predict_joins_trainer_stats_into_serving_data(data_dir: str) -> None:
    _ServeCapturingAlgo.captured_frame = None
    predict(data_path=data_dir, algorithm=_ServeCapturingAlgo())
    frame = _ServeCapturingAlgo.captured_frame
    assert frame is not None
    assert (
        "TrainerWinPercentage" in frame.columns
    )  # joined on TrainerId via build_serving_from_stats


# ================================================================
# test 6 — the built card carries no rating columns (ratings come only
#          from the per-horse stats join); predictions still produced
# ================================================================


def test_predict_card_drops_rating_columns_and_still_predicts(
    tmp_path: pathlib.Path,
) -> None:
    # Source race cards DO carry ratings — the built serving data must strip them.
    rows = [
        {
            "RaceId": 10,
            "HorseId": 101,
            "JockeyId": 201,
            "TrainerId": 301,
            "CourseId": 5,
            "CourseName": "Ascot",
            "Off": "05/21/2026 14:30:00",
            "HorseName": "Thunderbolt",
            "Surface": "Turf",
            "Going": "Good",
            "RaceType": "Flat",
            "DistanceInMeters": 1600.0,
            "WeightInPounds": 126.0,
            "OfficialRating": 80.0,
            "RacingPostRating": 100.0,
            "TopSpeedRating": 90.0,
        }
    ]
    _write_race_features(str(tmp_path))
    _write_horse_stats(str(tmp_path))
    _write_jockey_stats(str(tmp_path))
    _write_trainer_stats(str(tmp_path))
    _write_race_cards(str(tmp_path), rows=rows)

    _ServeCapturingAlgo.captured_frame = None
    result = predict(data_path=str(tmp_path), algorithm=_ServeCapturingAlgo())

    frame = _ServeCapturingAlgo.captured_frame
    for col in ["OfficialRating", "RacingPostRating", "TopSpeedRating"]:
        assert col not in frame.columns, (  # pyright: ignore[reportAttributeAccessIssue]  # predict() populates captured_frame at runtime
            f"rating column leaked into the serving data: {col}"
            f"rating column leaked into the serving data: {col}"
        )
    assert len(result) == 1  # prediction still produced


# ================================================================
# Staking (issues/002) — a Stake column riding from the full field
# ================================================================


class _FullFieldAlgo:
    """FieldPredictor stub that scores the WHOLE field with a per-horse
    WinProbability map, so the staking step's within-race normalization is
    exercised over the full field (not just the winner row)."""

    max_horses = 99

    def __init__(self, probs: dict[int, float], max_horses: int = 99):
        self.max_horses = max_horses
        self.probs = probs

    def fit(self, data: RaceData) -> None:
        pass

    def predict_field(self, data: RaceData) -> pd.DataFrame:
        frame = data.frame.copy()
        if frame.empty:
            return pd.DataFrame(
                columns=["RaceId", "HorseId", "WinProbability", "PredictedRank"]
            )
        frame["WinProbability"] = frame["HorseId"].map(self.probs)
        frame["PredictedRank"] = frame.groupby("RaceId")["WinProbability"].rank(
            method="first", ascending=False
        )
        return frame[["RaceId", "HorseId", "WinProbability", "PredictedRank"]]  # pyright: ignore[reportReturnType]  # column-list index yields DataFrame

    def predict(self, data: RaceData) -> pd.DataFrame:
        return self.predict_field(data)[["RaceId", "HorseId"]]  # pyright: ignore[reportReturnType]  # column-list index yields DataFrame


def _staking_card_row(
    horse_id: int,
    horse_name: str,
    jockey_id: int,
    forecast_odds: float,
    *,
    race_id: int = 10,
    course_name: str = "Ascot",
    off: str = "05/21/2026 14:30:00",
) -> dict[str, Any]:
    return {
        "RaceId": race_id,
        "HorseId": horse_id,
        "JockeyId": jockey_id,
        "TrainerId": 301,
        "CourseId": 5,
        "CourseName": course_name,
        "Off": off,
        "HorseName": horse_name,
        "Surface": "Turf",
        "Going": "Good",
        "RaceType": "Flat",
        "DistanceInMeters": 1600.0,
        "WeightInPounds": 126.0,
        "ForecastDecimalOdds": forecast_odds,
    }


def test_predict_value_bet_gets_full_field_normalized_stake(
    tmp_path: pathlib.Path,
) -> None:
    # One race, three runners. The model rates horse 101 (0.40) above its market
    # price (forecast 3.0 -> de-overround MarketProb ~ 0.339), so it clears the
    # value gate; the other two are at/below it. The stake is sized from the
    # FULL-field-normalized ModelProb (0.40), not the winner-row-only prob (1.0):
    #   f* = (0.40*3 - 1)/(3 - 1) = 0.1
    #   stake = min(0.25 * 0.1 * 120, 5) = 3.00
    # Winner-row-only normalization would instead give the capped 5.00 (f* = 1.0),
    # so the sub-cap 3.00 value is what proves the normalization spans the field.
    rows = [
        _staking_card_row(101, "Alpha", 201, 3.0),
        _staking_card_row(201, "Bravo", 202, 2.5),
        _staking_card_row(301, "Charlie", 203, 4.0),
    ]
    _write_race_features(str(tmp_path))
    _write_horse_stats(str(tmp_path))
    _write_jockey_stats(str(tmp_path))
    _write_trainer_stats(str(tmp_path))
    _write_race_cards(str(tmp_path), rows=rows)

    algo = _FullFieldAlgo(probs={101: 0.40, 201: 0.35, 301: 0.25})
    result = predict(data_path=str(tmp_path), algorithm=algo)

    assert "Stake" in result.columns
    winner = result[result["RaceId"] == 10].iloc[0]
    assert winner["HorseId"] == 101
    assert winner["Stake"] == 3.0


def test_predict_no_value_race_retained_with_zero_stake(
    tmp_path: pathlib.Path,
) -> None:
    # The model barely separates the two runners (0.51 vs 0.49) and agrees with
    # the market (both 2.0 → MarketProb 0.5/0.5), so the top pick's edge (0.01) is
    # below MIN_EDGE: no bet. The race must still appear, with Stake 0 — the file
    # stays a complete record of what was considered.
    rows = [
        _staking_card_row(
            401, "Delta", 201, 2.0, race_id=20, off="05/21/2026 15:00:00"
        ),
        _staking_card_row(501, "Echo", 202, 2.0, race_id=20, off="05/21/2026 15:00:00"),
    ]
    _write_race_features(str(tmp_path))
    _write_horse_stats(str(tmp_path))
    _write_jockey_stats(str(tmp_path))
    _write_trainer_stats(str(tmp_path))
    _write_race_cards(str(tmp_path), rows=rows)

    algo = _FullFieldAlgo(probs={401: 0.51, 501: 0.49})
    result = predict(data_path=str(tmp_path), algorithm=algo)

    assert len(result[result["RaceId"] == 20]) == 1  # race retained, not dropped
    winner = result[result["RaceId"] == 20].iloc[0]
    assert winner["HorseId"] == 401
    assert winner["Stake"] == 0.0
