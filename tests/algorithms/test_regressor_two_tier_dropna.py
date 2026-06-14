from typing import Any, ClassVar

import numpy as np
import pandas as pd

from race_analytics.algorithms.base import REQUIRED_PREDICTORS
from race_analytics.algorithms.regressor import RegressorAlgorithm
from race_analytics.features.race_data import RaceData, RaceDataBuilder


def _rd(df: pd.DataFrame) -> RaceData:
    return RaceDataBuilder().wrap_training(df)


class _CapturingEstimator:
    def __init__(self) -> None:
        self.fit_X: pd.DataFrame | None = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "_CapturingEstimator":
        self.fit_X = pd.DataFrame(X).copy()
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.zeros(len(X))


class _NanTolerantAlgo(RegressorAlgorithm):
    nan_tolerant_predictors: ClassVar[list[str]] = ["SomeCol"]

    def _create_model(self) -> Any:
        self._cap = _CapturingEstimator()
        return self._cap


_REQUIRED_COL = REQUIRED_PREDICTORS[0]  # "DistanceInMeters"


def _row(
    idx: int, some_col: float | None = 1.0, required_col: float | None = 1600.0
) -> dict[str, Any]:
    return {
        "RaceId": idx,
        "HorseId": idx,
        "Speed": 16.0,
        _REQUIRED_COL: required_col,
        "SomeCol": some_col,
    }


def test_nan_in_optional_col_is_kept_for_fitting() -> None:
    algo = _NanTolerantAlgo()
    rows = [_row(i) for i in range(7)]
    rows += [_row(i + 7, some_col=None) for i in range(3)]
    algo.fit(_rd(pd.DataFrame(rows)))
    # captured fit_X is set by fit; test reaches the capturing stub's private attr
    assert len(algo._cap.fit_X) == 10  # pyright: ignore[reportPrivateUsage, reportArgumentType]


def test_nan_in_required_col_is_dropped() -> None:
    algo = _NanTolerantAlgo()
    rows = [_row(i) for i in range(10)]
    rows += [_row(i + 10, required_col=None) for i in range(3)]
    algo.fit(_rd(pd.DataFrame(rows)))
    assert len(algo._cap.fit_X) == 10  # pyright: ignore[reportPrivateUsage, reportArgumentType]


def test_fitted_predictors_includes_optional_col() -> None:
    algo = _NanTolerantAlgo()
    rows = [_row(i) for i in range(5)]
    algo.fit(_rd(pd.DataFrame(rows)))
    # _fitted_predictors is the two-tier feature list set during fit
    assert "SomeCol" in algo._fitted_predictors  # pyright: ignore[reportPrivateUsage]
    assert _REQUIRED_COL in algo._fitted_predictors  # pyright: ignore[reportPrivateUsage]
