"""Engine-boundary tests for the RaceData template on FieldPredictorBaseAlgorithm (issue 003).

These exercise the new RaceData-based fit/predict_field/predict path with a fake
estimator over a hand-built RaceData. The legacy four-frame algorithms are covered
by their existing tests (run as part of the full suite) and must stay green — issue
003 adds the engine without migrating any subclass.
"""

import numpy as np
import pandas as pd
import pytest

from race_analytics.algorithms.base import (
    REQUIRED_PREDICTORS,
    AbstainCapable,
    FieldPredictor,
    FieldPredictorBaseAlgorithm,
)
from race_analytics.features.race_data import RaceData

_AS_OF = pd.Timestamp("2026-06-13")


class _FakeClassifier:
    """Decreasing predict_proba so horse[0] in each race ranks first."""

    def __init__(self) -> None:
        self.fit_X: pd.DataFrame | None = None
        self.fit_y: pd.Series | None = None
        self.fit_sw: np.ndarray | str | None = "unset"

    def fit(
        self, X: pd.DataFrame, y: pd.Series, sample_weight: np.ndarray | None = None
    ) -> "_FakeClassifier":
        self.fit_X = pd.DataFrame(X).copy()
        self.fit_y = y.copy() if hasattr(y, "copy") else y
        self.fit_sw = sample_weight
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        n = len(X)
        out = np.zeros((n, 2))
        out[:, 1] = np.arange(n, 0, -1) / n
        return out


class _EngineClassifier(FieldPredictorBaseAlgorithm):
    """Minimal engine subclass: only the estimator-fit and score hooks."""

    def __init__(
        self, clf: _FakeClassifier | None = None, max_horses: int = 10
    ) -> None:
        self._clf = clf or _FakeClassifier()
        super().__init__(max_horses)

    def _fit_estimator(
        self, X: pd.DataFrame, frame: pd.DataFrame, sample_weight: np.ndarray | None
    ) -> None:
        self._clf.fit(X, frame[self.label_col], sample_weight=sample_weight)

    def _score(self, X: pd.DataFrame) -> np.ndarray:
        return self._clf.predict_proba(X)[:, 1]


def _race_data(
    n_races: int = 2, horses: int = 3, with_label: bool = True, max_horses: int = 10
) -> RaceData:
    rows = []
    for r in range(1, n_races + 1):
        for h in range(horses):
            row = dict.fromkeys(REQUIRED_PREDICTORS, 1.0)
            row["RaceId"] = r
            row["HorseId"] = r * 10 + h
            if with_label:
                row["Wins"] = 1.0 if h == 0 else 0.0
            rows.append(row)
    return RaceData(pd.DataFrame(rows), _AS_OF, max_horses=max_horses)  # pyright: ignore[reportArgumentType]  # pd.Timestamp ctor return includes NaTType arm


def _fitted_engine(
    clf: _FakeClassifier | None = None, max_horses: int = 10
) -> _EngineClassifier:
    algo = _EngineClassifier(clf=clf, max_horses=max_horses)
    algo.fit(_race_data(with_label=True))
    return algo


def test_predict_field_empty_before_fit():
    algo = _EngineClassifier()
    result = algo.predict_field(_race_data(with_label=False))
    assert result.empty


def test_predict_field_returns_full_scored_field():
    algo = _fitted_engine()
    field = algo.predict_field(_race_data(n_races=2, horses=3, with_label=False))
    assert len(field) == 6
    assert "WinProbability" in field.columns
    assert "PredictedRank" in field.columns
    assert field["WinProbability"].notna().all()
    assert field["PredictedRank"].notna().all()


def test_predict_returns_top1_per_race():
    algo = _fitted_engine()
    preds = algo.predict(_race_data(n_races=2, horses=3, with_label=False))
    assert len(preds) == 2
    assert list(preds.columns) == ["RaceId", "HorseId"]
    assert set(preds["HorseId"]) == {10, 20}


def test_fit_selects_required_predictors_as_feature_cols():
    algo = _fitted_engine()
    assert set(algo._feature_cols) == set(REQUIRED_PREDICTORS)  # pyright: ignore[reportPrivateUsage]  # intentional internal-state assertion


def test_oversized_field_is_dropped():
    # max_horses is the algorithm's constructor param (matches legacy semantics)
    algo = _fitted_engine(max_horses=2)
    field = algo.predict_field(_race_data(n_races=1, horses=3, with_label=False))
    assert field.empty


def test_incomplete_race_dropped_when_a_runner_has_nan_required():
    algo = _fitted_engine()
    serve = _race_data(n_races=2, horses=3, with_label=False)
    serve.frame.loc[
        (serve.frame["RaceId"] == 1) & (serve.frame["HorseId"] == 12),
        "DistanceInMeters",
    ] = np.nan
    field = algo.predict_field(serve)
    assert set(field["RaceId"]) == {2}


def test_race_gate_override_filters_before_scoring():
    class _GatedEngine(_EngineClassifier):
        def _race_gate(self, data: RaceData) -> RaceData:
            return data.subset(data.frame["RaceId"] == 1)

    algo = _GatedEngine()
    algo.fit(_race_data(with_label=True))
    field = algo.predict_field(_race_data(n_races=2, horses=3, with_label=False))
    assert set(field["RaceId"]) == {1}


def test_sample_weight_hook_is_passed_to_estimator():
    class _WeightedEngine(_EngineClassifier):
        def _sample_weight(self, frame: pd.DataFrame) -> np.ndarray:
            return np.full(len(frame), 2.0)

    clf = _FakeClassifier()
    algo = _WeightedEngine(clf=clf)
    algo.fit(_race_data(with_label=True))
    assert clf.fit_sw is not None
    assert len(clf.fit_sw) == len(clf.fit_X)  # pyright: ignore[reportArgumentType]  # fit_X set during fit() above
    assert (clf.fit_sw == 2.0).all()  # pyright: ignore[reportAttributeAccessIssue]  # fit_sw is ndarray after fit()


def test_return_full_field_false_yields_only_rank1_rows():
    class _TopOnlyEngine(_EngineClassifier):
        return_full_field = False

    algo = _TopOnlyEngine()
    algo.fit(_race_data(with_label=True))
    field = algo.predict_field(_race_data(n_races=2, horses=3, with_label=False))
    assert len(field) == 2
    assert (field["PredictedRank"] == 1).all()


class _FakeRanker:
    """A ranker-style estimator: fit(group=...) and predict (no predict_proba)."""

    def __init__(self) -> None:
        self.fit_sw: np.ndarray | str | None = "unset"

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        group: np.ndarray | None = None,
        sample_weight: np.ndarray | None = None,
    ) -> "_FakeRanker":
        self.fit_sw = sample_weight
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.arange(len(X), 0, -1)


class _RankerEngine(FieldPredictorBaseAlgorithm):
    """Engine subclass scoring via a ranker's predict() instead of predict_proba()."""

    def __init__(self, max_horses: int = 10) -> None:
        self._r = _FakeRanker()
        super().__init__(max_horses)

    def _fit_estimator(
        self, X: pd.DataFrame, frame: pd.DataFrame, sample_weight: np.ndarray | None
    ) -> None:
        self._r.fit(X, frame[self.label_col], sample_weight=sample_weight)

    def _score(self, X: pd.DataFrame) -> np.ndarray:
        return self._r.predict(X)


class _WeightedClassifier(_EngineClassifier):
    def _sample_weight(self, frame: pd.DataFrame) -> np.ndarray:
        return np.full(len(frame), 3.0)


@pytest.mark.parametrize(
    "factory", [_EngineClassifier, _RankerEngine, _WeightedClassifier]
)
def test_engine_ranks_full_field_for_any_estimator_and_weighting(
    factory: type[FieldPredictorBaseAlgorithm],
) -> None:
    algo = factory()
    algo.fit(_race_data(with_label=True))
    field = algo.predict_field(_race_data(n_races=2, horses=3, with_label=False))

    assert len(field) == 6
    assert {"RaceId", "HorseId", "WinProbability", "PredictedRank"} <= set(
        field.columns
    )
    rank1_per_race = field.groupby("RaceId")["PredictedRank"].apply(
        lambda r: (r == 1).sum()
    )
    assert (rank1_per_race == 1).all()


def test_engine_satisfies_field_predictor_protocol():
    assert isinstance(_EngineClassifier(), FieldPredictor)


def test_abstain_capable_protocol_membership():
    class _Abstainer:
        def predict_field_unfiltered(self, data: RaceData) -> RaceData:
            return data

        def get_confidence_gate(self) -> None:
            return None

    assert isinstance(_Abstainer(), AbstainCapable)
    assert not isinstance(_EngineClassifier(), AbstainCapable)
