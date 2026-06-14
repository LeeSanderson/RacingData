import os
import pathlib

import pandas as pd
import pytest

from race_analytics.scripts.build_features import build_features


def _write_results(path: str) -> None:
    pd.DataFrame(
        [
            {
                "RaceId": 1,
                "Off": "07/20/2021 15:15:00",
                "HorseId": 101,
                "JockeyId": 201,
                "TrainerId": 301,
                "Surface": "Turf",
                "RaceType": "Flat",
                "Going": "Good",
                "DistanceInMeters": 1600.0,
                "RaceTimeInSeconds": 100.0,
                "WeightInPounds": 126.0,
                "FinishingPosition": 1,
                "DecimalOdds": 3.0,
                "OfficialRating": 80.0,
                "RacingPostRating": 100.0,
                "TopSpeedRating": 90.0,
            },
            {
                "RaceId": 1,
                "Off": "07/20/2021 15:15:00",
                "HorseId": 102,
                "JockeyId": 202,
                "TrainerId": 302,
                "Surface": "Turf",
                "RaceType": "Flat",
                "Going": "Good",
                "DistanceInMeters": 1600.0,
                "RaceTimeInSeconds": 105.0,
                "WeightInPounds": 124.0,
                "FinishingPosition": 2,
                "DecimalOdds": 5.0,
                "OfficialRating": 78.0,
                "RacingPostRating": 98.0,
                "TopSpeedRating": 88.0,
            },
        ]
    ).to_csv(os.path.join(path, "Results_2021_07.csv"), index=False)


@pytest.fixture
def data_dir(tmp_path: pathlib.Path) -> str:
    _write_results(str(tmp_path))
    return str(tmp_path)


def test_build_features_writes_all_four_csvs(data_dir: str) -> None:
    build_features(data_dir)
    for name in [
        "Race_Features.csv",
        "Horse_Stats.csv",
        "Jockey_Stats.csv",
        "Trainer_Stats.csv",
    ]:
        path = os.path.join(data_dir, name)
        assert os.path.exists(path), f"{name} was not created"
        assert len(pd.read_csv(path)) > 0, f"{name} is empty"
