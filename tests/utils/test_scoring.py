from typing import Any

import pandas as pd
import pytest

from race_analytics.utils.scoring import accuracy, roi


def _predictions(rows: list[tuple[Any, ...]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["RaceId", "HorseId"])


def _results(rows: list[tuple[Any, ...]]) -> pd.DataFrame:
    return pd.DataFrame(
        rows,
        columns=[
            "RaceId",
            "HorseId",
            "FinishingPosition",
            "DecimalOdds",
            "ResultStatus",
        ],
    )


def test_accuracy_all_correct() -> None:
    preds = _predictions([(1, 10), (2, 20)])
    results = _results(
        [
            (1, 10, 1, 3.0, "CompletedRace"),
            (2, 20, 1, 4.0, "CompletedRace"),
        ]
    )
    assert accuracy(preds, results) == pytest.approx(1.0)


def test_accuracy_all_wrong() -> None:
    preds = _predictions([(1, 10), (2, 20)])
    results = _results(
        [
            (1, 10, 2, 3.0, "CompletedRace"),
            (2, 20, 3, 4.0, "CompletedRace"),
        ]
    )
    assert accuracy(preds, results) == pytest.approx(0.0)


def test_accuracy_mixed() -> None:
    preds = _predictions([(1, 10), (2, 20)])
    results = _results(
        [
            (1, 10, 1, 5.0, "CompletedRace"),
            (2, 20, 2, 4.0, "CompletedRace"),
        ]
    )
    assert accuracy(preds, results) == pytest.approx(0.5)


def test_accuracy_excludes_void_races() -> None:
    # Race 1: correct and completed; Race 2: predicted but voided
    preds = _predictions([(1, 10), (2, 20)])
    results = _results(
        [
            (1, 10, 1, 4.0, "CompletedRace"),
            (2, 20, 0, 3.0, "NonRunner"),
        ]
    )
    # Only race 1 counts → 1/1 = 1.0
    assert accuracy(preds, results) == pytest.approx(1.0)


def test_roi_all_correct() -> None:
    # 2 races, odds 3.0 and 4.0, both correct
    # stakes=2, winnings=7.0, earnings=5.0
    preds = _predictions([(1, 10), (2, 20)])
    results = _results(
        [
            (1, 10, 1, 3.0, "CompletedRace"),
            (2, 20, 1, 4.0, "CompletedRace"),
        ]
    )
    assert roi(preds, results) == pytest.approx(5.0)


def test_roi_all_wrong() -> None:
    # 2 races, both wrong → winnings=0, earnings=-2.0
    preds = _predictions([(1, 10), (2, 20)])
    results = _results(
        [
            (1, 10, 2, 3.0, "CompletedRace"),
            (2, 20, 3, 4.0, "CompletedRace"),
        ]
    )
    assert roi(preds, results) == pytest.approx(-2.0)


def test_roi_mixed() -> None:
    # Race 1 correct (odds 5.0), Race 2 wrong
    # stakes=2, winnings=5.0, earnings=3.0
    preds = _predictions([(1, 10), (2, 20)])
    results = _results(
        [
            (1, 10, 1, 5.0, "CompletedRace"),
            (2, 20, 2, 4.0, "CompletedRace"),
        ]
    )
    assert roi(preds, results) == pytest.approx(3.0)


def test_roi_excludes_void_races() -> None:
    # Race 1: correct, completed (odds 4.0); Race 2: void (NonRunner)
    # Only race 1 counts: stakes=1, winnings=4.0, earnings=3.0
    preds = _predictions([(1, 10), (2, 20)])
    results = _results(
        [
            (1, 10, 1, 4.0, "CompletedRace"),
            (2, 20, 0, 3.0, "NonRunner"),
        ]
    )
    assert roi(preds, results) == pytest.approx(3.0)


def _results_with_forecast(rows: list[tuple[Any, ...]]) -> pd.DataFrame:
    return pd.DataFrame(
        rows,
        columns=[
            "RaceId",
            "HorseId",
            "FinishingPosition",
            "DecimalOdds",
            "ForecastDecimalOdds",
            "ResultStatus",
        ],
    )


def test_roi_values_winner_at_forecast_when_present() -> None:
    # Winner has a forecast price (2.0) that differs from its SP (3.0); the forecast
    # is preferred, so winnings=2.0, stakes=1, earnings=1.0.
    preds = _predictions([(1, 10)])
    results = _results_with_forecast([(1, 10, 1, 3.0, 2.0, "CompletedRace")])
    assert roi(preds, results) == pytest.approx(1.0)


def test_roi_falls_back_to_sp_when_forecast_absent() -> None:
    # Forecast column present but NaN for this winner -> resolver falls back to SP (5.0);
    # winnings=5.0, stakes=1, earnings=4.0.
    preds = _predictions([(1, 10)])
    results = _results_with_forecast([(1, 10, 1, 5.0, float("nan"), "CompletedRace")])
    assert roi(preds, results) == pytest.approx(4.0)
