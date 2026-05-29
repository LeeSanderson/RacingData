import numpy as np
import pandas as pd
from datetime import datetime

from race_analytics.algorithms.base import REQUIRED_PREDICTORS
from race_analytics.algorithms.binary_win_classifier import BinaryWinClassifierAlgorithm

_LONG_AGO = datetime(2020, 1, 1)
_REQ_COL = "DistanceInMeters"  # first entry of REQUIRED_PREDICTORS


class _MockClassifier:
    def __init__(self):
        self.fit_X = None
        self.fit_y = None

    def fit(self, X, y):
        self.fit_X = pd.DataFrame(X).copy()
        self.fit_y = y.copy() if hasattr(y, "copy") else y
        return self

    def predict_proba(self, X):
        n = len(X)
        probs = np.zeros((n, 2))
        probs[:, 1] = np.arange(n, 0, -1) / n  # distinct decreasing; horse[0] gets rank-1
        return probs


class _SpyAlgo(BinaryWinClassifierAlgorithm):
    extra_nan_tolerant_features = ["SomeRatingCol"]

    def __init__(self):
        self._mock = _MockClassifier()
        self._prepare_training_calls: list[pd.DataFrame] = []
        self._prepare_prediction_calls: list[pd.DataFrame] = []
        self._apply_gate_calls: list[pd.DataFrame] = []
        super().__init__(self._mock)

    def _prepare_training_df(self, train_df: pd.DataFrame) -> pd.DataFrame:
        self._prepare_training_calls.append(train_df.copy())
        return train_df

    def _prepare_prediction_df(self, merged: pd.DataFrame) -> pd.DataFrame:
        self._prepare_prediction_calls.append(merged.copy())
        return merged

    def _apply_gate(self, predictable: pd.DataFrame) -> pd.DataFrame:
        self._apply_gate_calls.append(predictable.copy())
        return predictable


def _train_row(race_id: int, horse_id: int, wins: int = 0,
               dist: float | None = 1600.0, some_rating: float | None = 90.0) -> dict:
    return {
        "RaceId": race_id,
        "HorseId": horse_id,
        "Wins": wins,
        _REQ_COL: dist,
        "SomeRatingCol": some_rating,
    }


def _race_row(race_id: int, horse_id: int, jockey_id: int) -> dict:
    return {
        "RaceId": race_id, "HorseId": horse_id, "JockeyId": jockey_id,
        "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
        _REQ_COL: 1600.0,
    }


def _horse_stat(horse_id: int, some_rating: float | None = 90.0) -> dict:
    return {
        "HorseId": horse_id,
        "LastOff": _LONG_AGO,
        "SomeRatingCol": some_rating,
    }


def _jockey_stat(jockey_id: int) -> dict:
    return {"JockeyId": jockey_id, "LastOff": _LONG_AGO}


def _make_train_df(n_races: int = 3, horses_per_race: int = 3) -> pd.DataFrame:
    rows = [
        _train_row(r, r * 10 + h, wins=1 if h == 0 else 0)
        for r in range(1, n_races + 1)
        for h in range(horses_per_race)
    ]
    return pd.DataFrame(rows)


def _make_predict_fixtures(n_horses: int = 3):
    races = pd.DataFrame([_race_row(99, h, h) for h in range(n_horses)])
    horse_stats = pd.DataFrame([_horse_stat(h) for h in range(n_horses)])
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in range(n_horses)])
    return races, horse_stats, jockey_stats


# ── Cycle 1: _prepare_training_df called once during fit ─────────────────────


def test_prepare_training_df_called_exactly_once_during_fit():
    spy = _SpyAlgo()
    spy.fit(_make_train_df())
    assert len(spy._prepare_training_calls) == 1


# ── Cycle 2: _prepare_training_df receives full frame before dropna ───────────


def test_prepare_training_df_sees_all_rows_including_those_dropped_by_dropna():
    spy = _SpyAlgo()
    rows = [
        _train_row(1, 10, wins=1),
        _train_row(1, 11, wins=0),
        _train_row(2, 20, wins=0, dist=None),  # NaN in required — will be dropped later
    ]
    spy.fit(pd.DataFrame(rows))

    assert len(spy._prepare_training_calls[0]) == 3  # all rows before dropna
    assert len(spy._mock.fit_X) == 2  # only 2 rows after dropna


# ── Cycle 3: _prepare_prediction_df called once during predict ────────────────


def test_prepare_prediction_df_called_exactly_once_during_predict():
    spy = _SpyAlgo()
    spy.fit(_make_train_df())
    races, horse_stats, jockey_stats = _make_predict_fixtures()
    spy.predict(races, horse_stats, jockey_stats)
    assert len(spy._prepare_prediction_calls) == 1


# ── Cycle 4: _apply_gate called after count gate, before scoring ──────────────


def test_apply_gate_called_with_count_columns_and_no_win_probability():
    spy = _SpyAlgo()
    spy.fit(_make_train_df())
    races, horse_stats, jockey_stats = _make_predict_fixtures()
    spy.predict(races, horse_stats, jockey_stats)

    assert len(spy._apply_gate_calls) == 1
    gate_frame = spy._apply_gate_calls[0]
    assert "OriginalCount" in gate_frame.columns
    assert "PredictableCount" in gate_frame.columns
    assert "WinProbability" not in gate_frame.columns


# ── Cycle 5: extra_nan_tolerant_features column tolerates NaN in fit ─────────


def test_nan_in_extra_tolerant_feature_is_kept_nan_in_required_is_dropped():
    spy = _SpyAlgo()
    rows = [
        _train_row(1, 10, wins=1),
        _train_row(1, 11, wins=0),
        _train_row(2, 20, wins=0, some_rating=None),   # NaN in extra — should survive
        _train_row(2, 21, wins=1),
        _train_row(3, 30, wins=0, dist=None),           # NaN in required — should drop
    ]
    spy.fit(pd.DataFrame(rows))

    assert len(spy._mock.fit_X) == 4            # horse 30 dropped; others kept
    assert "SomeRatingCol" in spy._mock.fit_X.columns
    assert spy._mock.fit_X["SomeRatingCol"].isna().sum() == 1  # horse 20's NaN survived
