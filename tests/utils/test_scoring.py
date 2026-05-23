import pandas as pd
import pytest

from race_analytics.utils.scoring import accuracy, roi


def _predictions(rows):
    return pd.DataFrame(rows, columns=["RaceId", "HorseId"])


def _results(rows):
    return pd.DataFrame(
        rows, columns=["RaceId", "HorseId", "FinishingPosition", "DecimalOdds", "ResultStatus"]
    )


def test_accuracy_all_correct():
    preds = _predictions([(1, 10), (2, 20)])
    results = _results([
        (1, 10, 1, 3.0, "CompletedRace"),
        (2, 20, 1, 4.0, "CompletedRace"),
    ])
    assert accuracy(preds, results) == pytest.approx(1.0)


def test_accuracy_all_wrong():
    preds = _predictions([(1, 10), (2, 20)])
    results = _results([
        (1, 10, 2, 3.0, "CompletedRace"),
        (2, 20, 3, 4.0, "CompletedRace"),
    ])
    assert accuracy(preds, results) == pytest.approx(0.0)


def test_accuracy_mixed():
    preds = _predictions([(1, 10), (2, 20)])
    results = _results([
        (1, 10, 1, 5.0, "CompletedRace"),
        (2, 20, 2, 4.0, "CompletedRace"),
    ])
    assert accuracy(preds, results) == pytest.approx(0.5)


def test_accuracy_excludes_void_races():
    # Race 1: correct and completed; Race 2: predicted but voided
    preds = _predictions([(1, 10), (2, 20)])
    results = _results([
        (1, 10, 1, 4.0, "CompletedRace"),
        (2, 20, 0, 3.0, "NonRunner"),
    ])
    # Only race 1 counts → 1/1 = 1.0
    assert accuracy(preds, results) == pytest.approx(1.0)


def test_roi_all_correct():
    # 2 races, odds 3.0 and 4.0, both correct
    # stakes=2, winnings=7.0, earnings=5.0
    preds = _predictions([(1, 10), (2, 20)])
    results = _results([
        (1, 10, 1, 3.0, "CompletedRace"),
        (2, 20, 1, 4.0, "CompletedRace"),
    ])
    assert roi(preds, results) == pytest.approx(5.0)


def test_roi_all_wrong():
    # 2 races, both wrong → winnings=0, earnings=-2.0
    preds = _predictions([(1, 10), (2, 20)])
    results = _results([
        (1, 10, 2, 3.0, "CompletedRace"),
        (2, 20, 3, 4.0, "CompletedRace"),
    ])
    assert roi(preds, results) == pytest.approx(-2.0)


def test_roi_mixed():
    # Race 1 correct (odds 5.0), Race 2 wrong
    # stakes=2, winnings=5.0, earnings=3.0
    preds = _predictions([(1, 10), (2, 20)])
    results = _results([
        (1, 10, 1, 5.0, "CompletedRace"),
        (2, 20, 2, 4.0, "CompletedRace"),
    ])
    assert roi(preds, results) == pytest.approx(3.0)


def test_roi_excludes_void_races():
    # Race 1: correct, completed (odds 4.0); Race 2: void (NonRunner)
    # Only race 1 counts: stakes=1, winnings=4.0, earnings=3.0
    preds = _predictions([(1, 10), (2, 20)])
    results = _results([
        (1, 10, 1, 4.0, "CompletedRace"),
        (2, 20, 0, 3.0, "NonRunner"),
    ])
    assert roi(preds, results) == pytest.approx(3.0)
