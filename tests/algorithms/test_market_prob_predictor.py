"""MarketProb exposed as an optional predictor (issue 004).

Behavioural cover for the wiring that lets every algorithm family pick up the
market-implied win probability through the shared feature-universe selection:

  * `MarketProb` lives in the shared ``OPTIONAL_PREDICTORS`` list;
  * the win-classifier family selects it via ``_feature_universe``;
  * the regressor family (incl. Ridge, whose ``nan_tolerant_predictors`` is empty)
    selects it too, and the dense uniform-prior column means no NaN reaches the
    estimator;
  * adding the feature introduces no odds-presence race gate — the predicted
    population is unchanged whether the column is present or not.
"""

from typing import Any

import numpy as np
import pandas as pd

from race_analytics.algorithms.base import OPTIONAL_PREDICTORS, REQUIRED_PREDICTORS
from race_analytics.algorithms.binary_win_classifier import BinaryWinClassifierAlgorithm
from race_analytics.algorithms.regressor import RegressorAlgorithm
from race_analytics.algorithms.ridge_regression import RidgeRegressionAlgorithm
from race_analytics.features.market_prob import MARKET_PROB, add_market_prob
from race_analytics.features.race_data import RaceData

_AS_OF = pd.Timestamp("2026-06-17")


class _FakeClassifier:
    """Decreasing predict_proba so horse[0] in each race ranks first; records fit_X."""

    def __init__(self) -> None:
        self.fit_X: pd.DataFrame | None = None

    def fit(
        self, X: pd.DataFrame, y: pd.Series, sample_weight: np.ndarray | None = None
    ) -> "_FakeClassifier":
        self.fit_X = pd.DataFrame(X).copy()
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        n = len(X)
        out = np.zeros((n, 2))
        out[:, 1] = np.arange(n, 0, -1) / n
        return out


def _race_data(
    *,
    odds: dict[tuple[int, int], float] | None = None,
    label_col: str | None = "Wins",
    n_races: int = 2,
    horses: int = 3,
) -> RaceData:
    """A complete RaceData with every required predictor present.

    When ``odds`` is supplied (keyed by (RaceId, HorseId) -> decimal odds), a
    ``MarketProb`` column is materialised through the real ``add_market_prob`` helper
    so missing entries exercise the uniform-prior imputation. When ``odds`` is None no
    odds/MarketProb column exists at all — the no-column baseline. ``label_col`` picks
    the training label ("Wins" for classifiers, "Speed" for regressors; None to serve).
    """
    rows: list[dict[str, Any]] = []
    for r in range(1, n_races + 1):
        for h in range(horses):
            row = dict.fromkeys(REQUIRED_PREDICTORS, 1.0)
            row["RaceId"] = r
            row["HorseId"] = r * 10 + h
            if label_col == "Wins":
                row[label_col] = 1.0 if h == 0 else 0.0
            elif label_col is not None:
                row[label_col] = 14.0 + h
            if odds is not None:
                row["DecimalOdds"] = odds.get((r, r * 10 + h), np.nan)
            rows.append(row)
    frame = pd.DataFrame(rows)
    if odds is not None:
        frame = add_market_prob(frame)
    return RaceData(frame, _AS_OF)  # pyright: ignore[reportArgumentType]  # pd.Timestamp ctor return includes NaTType arm


def _fit_win_classifier(data: RaceData) -> BinaryWinClassifierAlgorithm:
    algo = BinaryWinClassifierAlgorithm(_FakeClassifier())
    algo.fit(data)
    return algo


def test_market_prob_is_a_shared_optional_predictor() -> None:
    assert MARKET_PROB in OPTIONAL_PREDICTORS


def test_win_classifier_selects_market_prob_when_present() -> None:
    algo = _fit_win_classifier(_race_data(odds={(1, 10): 2.0, (1, 11): 3.0}))
    assert MARKET_PROB in algo._feature_cols  # pyright: ignore[reportPrivateUsage]  # intentional internal-state assertion


def test_ridge_regressor_selects_market_prob_when_present() -> None:
    # Ridge has empty nan_tolerant_predictors, so it would skip every other optional
    # predictor — MarketProb is the one optional feature the regressor always takes.
    algo = RidgeRegressionAlgorithm()
    algo.fit(_race_data(odds={(1, 10): 2.0, (1, 11): 3.0}, label_col="Speed"))
    assert MARKET_PROB in algo._fitted_predictors  # pyright: ignore[reportPrivateUsage]  # intentional internal-state assertion


class _CapturingRegressor(RegressorAlgorithm):
    """A plain regressor (no nan_tolerant_predictors) that records its fit matrix."""

    def _create_model(self) -> Any:
        self._cap = _CapturingEstimator()
        return self._cap


class _CapturingEstimator:
    def __init__(self) -> None:
        self.fit_X: pd.DataFrame | None = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "_CapturingEstimator":
        self.fit_X = pd.DataFrame(X).copy()
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.zeros(len(X))


def test_regressor_estimator_receives_dense_market_prob() -> None:
    # Horse (1, 11) has no odds -> uniform-prior imputation must keep MarketProb dense
    # so no NaN reaches the estimator even though the runner was unpriced.
    algo = _CapturingRegressor()
    algo.fit(_race_data(odds={(1, 10): 2.0}, label_col="Speed"))
    fit_X = algo._cap.fit_X  # pyright: ignore[reportPrivateUsage]
    assert fit_X is not None
    assert MARKET_PROB in fit_X.columns
    assert fit_X[MARKET_PROB].notna().all()


def _population(field: pd.DataFrame) -> list[tuple[int, int]]:
    return sorted(
        (int(r), int(h)) for r, h in zip(field["RaceId"], field["HorseId"], strict=True)
    )


def test_predicted_population_unchanged_and_no_odds_gate() -> None:
    priced = {(1, 10): 2.0, (1, 11): 3.0, (1, 12): 4.0}

    with_algo = _fit_win_classifier(_race_data(odds=priced))
    with_field = with_algo.predict_field(_race_data(odds=priced, label_col=None))

    without_algo = _fit_win_classifier(_race_data())
    without_field = without_algo.predict_field(_race_data(label_col=None))

    # Adding the feature shifts no race in or out of the predicted population.
    assert _population(with_field) == _population(without_field)
    # All six runners across both races are predicted — the fully-unpriced race 2
    # survives, proving no odds-presence gate was introduced.
    assert _population(with_field) == [
        (1, 10),
        (1, 11),
        (1, 12),
        (2, 20),
        (2, 21),
        (2, 22),
    ]
