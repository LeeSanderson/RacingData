import os
import pandas as pd
import pytest

from race_analytics.scripts.predict import predict


# ================================================================
# Shared fake algorithm and fixture helpers
# ================================================================

class _FakeAlgo:
    max_horses = 99

    def fit(self, train_df: pd.DataFrame) -> None:
        pass

    def predict(self, races: pd.DataFrame, horse_stats: pd.DataFrame, jockey_stats: pd.DataFrame) -> pd.DataFrame:
        if races.empty:
            return pd.DataFrame(columns=["RaceId", "HorseId"])
        return races.groupby("RaceId").first().reset_index()[["RaceId", "HorseId"]]


def _write_race_features(path: str) -> None:
    pd.DataFrame([{
        "RaceId": 1, "HorseId": 101, "Speed": 15.0,
        "DistanceInMeters": 1600.0, "WeightInPounds": 126.0,
    }]).to_csv(os.path.join(path, "Race_Features.csv"), index=False)


def _write_horse_stats(path: str) -> None:
    pd.DataFrame([{"HorseId": 101, "LastOff": "2026-01-01 00:00:00"}]).to_csv(
        os.path.join(path, "Horse_Stats.csv"), index=False
    )


def _write_jockey_stats(path: str) -> None:
    pd.DataFrame([{"JockeyId": 201, "LastOff": "2026-01-01 00:00:00"}]).to_csv(
        os.path.join(path, "Jockey_Stats.csv"), index=False
    )


def _write_race_cards(path: str, rows: list | None = None) -> None:
    if rows is None:
        rows = [{
            "RaceId": 10, "HorseId": 101, "JockeyId": 201,
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
    _write_race_cards(str(tmp_path))
    return str(tmp_path)


# ================================================================
# test 1 — output file is created
# ================================================================

def test_predict_writes_todayspredictions_csv(data_dir):
    predict(data_path=data_dir, algorithm=_FakeAlgo())
    assert os.path.exists(os.path.join(data_dir, "TodaysPredictions.csv"))


# ================================================================
# test 2 — output has correct columns
# ================================================================

def test_predict_output_has_correct_columns(data_dir):
    predict(data_path=data_dir, algorithm=_FakeAlgo())
    result = pd.read_csv(os.path.join(data_dir, "TodaysPredictions.csv"))
    assert list(result.columns) == ["RaceId", "CourseId", "CourseName", "Off", "HorseId", "HorseName"]


# ================================================================
# test 3 — output is sorted by CourseName then Off
# ================================================================

def test_predict_output_is_sorted_by_coursename_off(tmp_path):
    rows = [
        {"RaceId": 10, "HorseId": 101, "JockeyId": 201,
         "CourseId": 5, "CourseName": "York",
         "Off": "05/21/2026 15:00:00", "HorseName": "Alpha",
         "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
         "DistanceInMeters": 1600.0, "WeightInPounds": 126.0},
        {"RaceId": 20, "HorseId": 201, "JockeyId": 202,
         "CourseId": 3, "CourseName": "Ascot",
         "Off": "05/21/2026 14:00:00", "HorseName": "Beta",
         "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
         "DistanceInMeters": 1600.0, "WeightInPounds": 126.0},
        {"RaceId": 30, "HorseId": 301, "JockeyId": 203,
         "CourseId": 3, "CourseName": "Ascot",
         "Off": "05/21/2026 13:00:00", "HorseName": "Gamma",
         "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
         "DistanceInMeters": 1600.0, "WeightInPounds": 126.0},
    ]
    _write_race_features(str(tmp_path))
    _write_horse_stats(str(tmp_path))
    _write_jockey_stats(str(tmp_path))
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
    def fit(self, train_df): pass
    def predict(self, races, horse_stats, jockey_stats):
        return pd.DataFrame(columns=["RaceId", "HorseId"])


def test_predict_empty_winners_writes_empty_csv(data_dir):
    predict(data_path=data_dir, algorithm=_EmptyAlgo())
    result = pd.read_csv(os.path.join(data_dir, "TodaysPredictions.csv"))
    assert list(result.columns) == ["RaceId", "CourseId", "CourseName", "Off", "HorseId", "HorseName"]
    assert len(result) == 0
