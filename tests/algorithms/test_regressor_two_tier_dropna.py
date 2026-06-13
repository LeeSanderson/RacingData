import numpy as np
import pandas as pd
from race_analytics.algorithms.base import REQUIRED_PREDICTORS
from race_analytics.algorithms.regressor import RegressorAlgorithm
from race_analytics.features.race_data import RaceDataBuilder


def _rd(df):
    return RaceDataBuilder().wrap_training(df)


class _CapturingEstimator:
    def __init__(self):
        self.fit_X = None

    def fit(self, X, y):
        self.fit_X = pd.DataFrame(X).copy()
        return self

    def predict(self, X):
        return np.zeros(len(X))


class _NanTolerantAlgo(RegressorAlgorithm):
    nan_tolerant_predictors = ["SomeCol"]

    def _create_model(self):
        self._cap = _CapturingEstimator()
        return self._cap


_REQUIRED_COL = REQUIRED_PREDICTORS[0]  # "DistanceInMeters"


def _row(idx, some_col=1.0, required_col=1600.0):
    return {
        "RaceId": idx,
        "HorseId": idx,
        "Speed": 16.0,
        _REQUIRED_COL: required_col,
        "SomeCol": some_col,
    }


def test_nan_in_optional_col_is_kept_for_fitting():
    algo = _NanTolerantAlgo()
    rows = [_row(i) for i in range(7)]
    rows += [_row(i + 7, some_col=None) for i in range(3)]
    algo.fit(_rd(pd.DataFrame(rows)))
    assert len(algo._cap.fit_X) == 10


def test_nan_in_required_col_is_dropped():
    algo = _NanTolerantAlgo()
    rows = [_row(i) for i in range(10)]
    rows += [_row(i + 10, required_col=None) for i in range(3)]
    algo.fit(_rd(pd.DataFrame(rows)))
    assert len(algo._cap.fit_X) == 10


def test_fitted_predictors_includes_optional_col():
    algo = _NanTolerantAlgo()
    rows = [_row(i) for i in range(5)]
    algo.fit(_rd(pd.DataFrame(rows)))
    assert "SomeCol" in algo._fitted_predictors
    assert _REQUIRED_COL in algo._fitted_predictors
