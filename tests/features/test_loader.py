import pytest
import pandas as pd
from pathlib import Path

from race_analytics.features.loader import (
    load_results,
    load_race_cards,
    load_stats,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_OFF_FMT = "%m/%d/%Y %H:%M:%S"


def _write_results_csv(path: Path, rows: list[dict]) -> None:
    pd.DataFrame(rows).to_csv(path, index=False)


def _race_row(race_id: int, off: str, status: str = "CompletedRace") -> dict:
    return {"RaceId": race_id, "Off": off, "ResultStatus": status}


# ---------------------------------------------------------------------------
# load_results
# ---------------------------------------------------------------------------


def test_load_results_concatenates_multiple_files(tmp_path):
    _write_results_csv(tmp_path / "Results_202601.csv", [
        _race_row(1, "01/10/2026 14:00:00"),
        _race_row(2, "01/10/2026 15:00:00"),
    ])
    _write_results_csv(tmp_path / "Results_202602.csv", [
        _race_row(3, "02/05/2026 13:00:00"),
    ])
    df = load_results(tmp_path)
    assert len(df) == 3
    assert set(df["RaceId"]) == {1, 2, 3}


def test_load_results_sorted_chronologically(tmp_path):
    # Feb file written first, then Jan — output must still be chronological
    _write_results_csv(tmp_path / "Results_202602.csv", [
        _race_row(3, "02/05/2026 13:00:00"),
    ])
    _write_results_csv(tmp_path / "Results_202601.csv", [
        _race_row(1, "01/10/2026 14:00:00"),
        _race_row(2, "01/20/2026 15:00:00"),
    ])
    df = load_results(tmp_path)
    assert df["Off"].is_monotonic_increasing
    assert df["RaceId"].tolist() == [1, 2, 3]


def test_load_results_off_column_is_datetime(tmp_path):
    _write_results_csv(tmp_path / "Results_202601.csv", [
        _race_row(1, "01/10/2026 14:00:00"),
    ])
    df = load_results(tmp_path)
    assert pd.api.types.is_datetime64_any_dtype(df["Off"])


def test_load_results_raises_when_no_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_results(tmp_path)


# ---------------------------------------------------------------------------
# load_race_cards
# ---------------------------------------------------------------------------


def test_load_race_cards_returns_dataframe(tmp_path):
    pd.DataFrame([
        {"RaceId": 10, "Off": "05/26/2026 14:00:00", "HorseId": 100},
    ]).to_csv(tmp_path / "TodaysRaceCards.csv", index=False)
    df = load_race_cards(tmp_path)
    assert len(df) == 1
    assert df.iloc[0]["RaceId"] == 10


def test_load_race_cards_off_column_is_datetime(tmp_path):
    pd.DataFrame([{"RaceId": 10, "Off": "05/26/2026 14:00:00"}]).to_csv(
        tmp_path / "TodaysRaceCards.csv", index=False
    )
    df = load_race_cards(tmp_path)
    assert pd.api.types.is_datetime64_any_dtype(df["Off"])


def test_load_race_cards_raises_when_file_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_race_cards(tmp_path)


# ---------------------------------------------------------------------------
# load_stats
# ---------------------------------------------------------------------------


def test_load_stats_returns_correct_file(tmp_path):
    pd.DataFrame([{"HorseId": 1, "LastOff": "2026-01-10 14:00:00"}]).to_csv(
        tmp_path / "Horse_Stats.csv", index=False
    )
    df = load_stats(tmp_path, "Horse_Stats.csv")
    assert len(df) == 1
    assert "HorseId" in df.columns


def test_load_stats_raises_when_file_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_stats(tmp_path, "Horse_Stats.csv")


def test_load_stats_loads_each_standard_stats_file(tmp_path):
    for name in ("Race_Features.csv", "Horse_Stats.csv", "Jockey_Stats.csv", "Trainer_Stats.csv"):
        pd.DataFrame([{"Id": 1}]).to_csv(tmp_path / name, index=False)
        df = load_stats(tmp_path, name)
        assert len(df) == 1
