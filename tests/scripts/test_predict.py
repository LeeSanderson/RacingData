import os
import pandas as pd
import pytest

from race_analytics.scripts.predict import predict


# ================================================================
# Shared fake algorithms (FieldPredictor contract) and fixtures
# ================================================================

class _FakeAlgo:
    """FieldPredictor stub: one rank-1 pick per race with a fixed WinProbability."""

    max_horses = 99

    def __init__(self, max_horses: int = 99):
        self.max_horses = max_horses

    def fit(self, data) -> None:
        pass

    def predict_field(self, data) -> pd.DataFrame:
        frame = data.frame
        if frame.empty:
            return pd.DataFrame(columns=["RaceId", "HorseId", "WinProbability", "PredictedRank"])
        out = frame.groupby("RaceId").first().reset_index()[["RaceId", "HorseId"]].copy()
        out["WinProbability"] = 0.5
        out["PredictedRank"] = 1.0
        return out

    def predict(self, data) -> pd.DataFrame:
        return self.predict_field(data)[["RaceId", "HorseId"]]


def _write_race_features(path: str) -> None:
    pd.DataFrame([{
        "RaceId": 1, "HorseId": 101, "Speed": 15.0,
        "DistanceInMeters": 1600.0, "WeightInPounds": 126.0,
    }]).to_csv(os.path.join(path, "Race_Features.csv"), index=False)


def _write_horse_stats(path: str) -> None:
    pd.DataFrame([
        {"HorseId": 101, "LastOff": "2026-01-01 00:00:00"},
        {"HorseId": 201, "LastOff": "2026-01-01 00:00:00"},
        {"HorseId": 301, "LastOff": "2026-01-01 00:00:00"},
    ]).to_csv(os.path.join(path, "Horse_Stats.csv"), index=False)


def _write_jockey_stats(path: str) -> None:
    pd.DataFrame([
        {"JockeyId": 201, "LastOff": "2026-01-01 00:00:00"},
        {"JockeyId": 202, "LastOff": "2026-01-01 00:00:00"},
        {"JockeyId": 203, "LastOff": "2026-01-01 00:00:00"},
    ]).to_csv(os.path.join(path, "Jockey_Stats.csv"), index=False)


def _write_trainer_stats(path: str) -> None:
    pd.DataFrame([{
        "TrainerId": 301,
        "TrainerNumberOfPriorRaces": 5.0,
        "TrainerWinPercentage": 0.2,
        "TrainerTop3Percentage": 0.6,
        "TrainerAvgRelFinishingPosition": 0.4,
    }]).to_csv(os.path.join(path, "Trainer_Stats.csv"), index=False)


def _write_race_cards(path: str, rows: list | None = None) -> None:
    if rows is None:
        rows = [{
            "RaceId": 10, "HorseId": 101, "JockeyId": 201, "TrainerId": 301,
            "CourseId": 5, "CourseName": "Ascot",
            "Off": "05/21/2026 14:30:00",
            "HorseName": "Thunderbolt",
            "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
            "DistanceInMeters": 1600.0, "WeightInPounds": 126.0,
        }]
    pd.DataFrame(rows).to_csv(os.path.join(path, "TodaysRaceCards.csv"), index=False)


@pytest.fixture
def data_dir(tmp_path):
    _write_race_features(str(tmp_path))
    _write_horse_stats(str(tmp_path))
    _write_jockey_stats(str(tmp_path))
    _write_trainer_stats(str(tmp_path))
    _write_race_cards(str(tmp_path))
    return str(tmp_path)


# ================================================================
# test 1 — output file is created
# ================================================================

def test_predict_writes_todayspredictions_csv(data_dir):
    predict(data_path=data_dir, algorithm=_FakeAlgo())
    assert os.path.exists(os.path.join(data_dir, "TodaysPredictions.csv"))


# ================================================================
# test 2 — output has correct columns (predict_field carries WinProbability)
# ================================================================

def test_predict_output_has_correct_columns(data_dir):
    predict(data_path=data_dir, algorithm=_FakeAlgo())
    result = pd.read_csv(os.path.join(data_dir, "TodaysPredictions.csv"))
    assert list(result.columns) == [
        "RaceId", "CourseId", "CourseName", "Off", "HorseId", "HorseName", "WinProbability"
    ]


# ================================================================
# test 3 — output is sorted by CourseName then Off
# ================================================================

def test_predict_output_is_sorted_by_coursename_off(tmp_path):
    rows = [
        {"RaceId": 10, "HorseId": 101, "JockeyId": 201, "TrainerId": 301,
         "CourseId": 5, "CourseName": "York",
         "Off": "05/21/2026 15:00:00", "HorseName": "Alpha",
         "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
         "DistanceInMeters": 1600.0, "WeightInPounds": 126.0},
        {"RaceId": 20, "HorseId": 201, "JockeyId": 202, "TrainerId": 301,
         "CourseId": 3, "CourseName": "Ascot",
         "Off": "05/21/2026 14:00:00", "HorseName": "Beta",
         "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
         "DistanceInMeters": 1600.0, "WeightInPounds": 126.0},
        {"RaceId": 30, "HorseId": 301, "JockeyId": 203, "TrainerId": 301,
         "CourseId": 3, "CourseName": "Ascot",
         "Off": "05/21/2026 13:00:00", "HorseName": "Gamma",
         "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
         "DistanceInMeters": 1600.0, "WeightInPounds": 126.0},
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

    def fit(self, data):
        pass

    def predict_field(self, data):
        return pd.DataFrame(columns=["RaceId", "HorseId", "WinProbability", "PredictedRank"])

    def predict(self, data):
        return pd.DataFrame(columns=["RaceId", "HorseId"])


def test_predict_empty_winners_writes_empty_csv(data_dir):
    predict(data_path=data_dir, algorithm=_EmptyAlgo())
    result = pd.read_csv(os.path.join(data_dir, "TodaysPredictions.csv"))
    assert list(result.columns) == ["RaceId", "CourseId", "CourseName", "Off", "HorseId", "HorseName", "WinProbability"]
    assert len(result) == 0


# ================================================================
# test 5 — trainer stats reach the serving RaceData (joined on TrainerId)
# ================================================================

class _ServeCapturingAlgo:
    """Captures the serving RaceData so tests can inspect what predict.py built."""

    max_horses = 99
    captured_frame = None

    def __init__(self, max_horses: int = 99):
        self.max_horses = max_horses

    def fit(self, data):
        pass

    def predict_field(self, data):
        type(self).captured_frame = data.frame
        frame = data.frame
        if frame.empty:
            return pd.DataFrame(columns=["RaceId", "HorseId", "WinProbability", "PredictedRank"])
        out = frame.groupby("RaceId").first().reset_index()[["RaceId", "HorseId"]].copy()
        out["WinProbability"] = 0.5
        out["PredictedRank"] = 1.0
        return out

    def predict(self, data):
        return self.predict_field(data)[["RaceId", "HorseId"]]


def test_predict_joins_trainer_stats_into_serving_data(data_dir):
    _ServeCapturingAlgo.captured_frame = None
    predict(data_path=data_dir, algorithm=_ServeCapturingAlgo())
    frame = _ServeCapturingAlgo.captured_frame
    assert frame is not None
    assert "TrainerWinPercentage" in frame.columns  # joined on TrainerId via build_serving_from_stats


# ================================================================
# test 6 — the built card carries no rating columns (ratings come only
#          from the per-horse stats join); predictions still produced
# ================================================================

def test_predict_card_drops_rating_columns_and_still_predicts(tmp_path):
    # Source race cards DO carry ratings — the built serving data must strip them.
    rows = [{
        "RaceId": 10, "HorseId": 101, "JockeyId": 201, "TrainerId": 301,
        "CourseId": 5, "CourseName": "Ascot",
        "Off": "05/21/2026 14:30:00", "HorseName": "Thunderbolt",
        "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
        "DistanceInMeters": 1600.0, "WeightInPounds": 126.0,
        "OfficialRating": 80.0, "RacingPostRating": 100.0, "TopSpeedRating": 90.0,
    }]
    _write_race_features(str(tmp_path))
    _write_horse_stats(str(tmp_path))
    _write_jockey_stats(str(tmp_path))
    _write_trainer_stats(str(tmp_path))
    _write_race_cards(str(tmp_path), rows=rows)

    _ServeCapturingAlgo.captured_frame = None
    result = predict(data_path=str(tmp_path), algorithm=_ServeCapturingAlgo())

    frame = _ServeCapturingAlgo.captured_frame
    for col in ["OfficialRating", "RacingPostRating", "TopSpeedRating"]:
        assert col not in frame.columns, f"rating column leaked into the serving data: {col}"
    assert len(result) == 1  # prediction still produced
