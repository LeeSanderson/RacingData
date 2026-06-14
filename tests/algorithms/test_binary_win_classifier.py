"""Behaviour tests for BinaryWinClassifierAlgorithm on the RaceData engine (issue 004).

These drive the algorithm through its public API — `fit(train_df)` and the four-frame
`predict_field`/`predict` (adapted to RaceData by the base engine) — with a mock
estimator. Generic engine mechanics (race-gate ordering, sample weighting, top-1
shaping) live in `test_field_predictor_engine.py`; here we pin the win-classifier's
own behaviour: the engineered race context, NaN handling, and full-field/top-1 output.
"""

from datetime import datetime
from typing import Any, ClassVar

import numpy as np
import pandas as pd

from race_analytics.algorithms.binary_win_classifier import BinaryWinClassifierAlgorithm
from race_analytics.features.race_data import RaceData, RaceDataBuilder

_LONG_AGO = datetime(2020, 1, 1)
_AS_OF = datetime(2026, 1, 1)
_REQ_COL = "DistanceInMeters"  # first entry of REQUIRED_PREDICTORS


def _rd(df: pd.DataFrame) -> RaceData:
    return RaceDataBuilder().wrap_training(df)


def _serve(
    races: pd.DataFrame, horse_stats: pd.DataFrame, jockey_stats: pd.DataFrame
) -> RaceData:
    return RaceDataBuilder().build_serving_from_stats(
        races,
        horse_stats,
        jockey_stats,
        None,
        as_of=_AS_OF,  # pyright: ignore[reportArgumentType]  # datetime accepted as Timestamp at runtime
    )


class _MockClassifier:
    def __init__(self) -> None:
        self.fit_X: pd.DataFrame | None = None
        self.fit_y: Any = None
        self.fit_sw: Any = "unset"

    def fit(
        self, X: pd.DataFrame, y: pd.Series, sample_weight: np.ndarray | None = None
    ) -> "_MockClassifier":
        self.fit_X = pd.DataFrame(X).copy()
        self.fit_y = y.copy() if hasattr(y, "copy") else y
        self.fit_sw = sample_weight
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        n = len(X)
        probs = np.zeros((n, 2))
        probs[:, 1] = (
            np.arange(n, 0, -1) / n
        )  # distinct decreasing; horse[0] gets rank-1
        return probs


class _SpyAlgo(BinaryWinClassifierAlgorithm):
    extra_nan_tolerant_features: ClassVar[list[str]] = ["SomeRatingCol"]

    def __init__(self) -> None:
        self._mock = _MockClassifier()
        super().__init__(self._mock)


def _train_row(
    race_id: int,
    horse_id: int,
    wins: int = 0,
    dist: float | None = 1600.0,
    some_rating: float | None = 90.0,
) -> dict[str, Any]:
    return {
        "RaceId": race_id,
        "HorseId": horse_id,
        "Wins": wins,
        _REQ_COL: dist,
        "SomeRatingCol": some_rating,
    }


def _race_row(race_id: int, horse_id: int, jockey_id: int) -> dict[str, Any]:
    return {
        "RaceId": race_id,
        "HorseId": horse_id,
        "JockeyId": jockey_id,
        "Surface": "Turf",
        "Going": "Good",
        "RaceType": "Flat",
        _REQ_COL: 1600.0,
    }


def _horse_stat(horse_id: int, some_rating: float | None = 90.0) -> dict[str, Any]:
    return {
        "HorseId": horse_id,
        "LastOff": _LONG_AGO,
        "SomeRatingCol": some_rating,
    }


def _jockey_stat(jockey_id: int) -> dict[str, Any]:
    return {"JockeyId": jockey_id, "LastOff": _LONG_AGO}


def _make_train_df(n_races: int = 3, horses_per_race: int = 3) -> pd.DataFrame:
    rows = [
        _train_row(r, r * 10 + h, wins=1 if h == 0 else 0)
        for r in range(1, n_races + 1)
        for h in range(horses_per_race)
    ]
    return pd.DataFrame(rows)


def _make_predict_fixtures(
    n_horses: int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    races = pd.DataFrame([_race_row(99, h, h) for h in range(n_horses)])
    horse_stats = pd.DataFrame([_horse_stat(h) for h in range(n_horses)])
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in range(n_horses)])
    return races, horse_stats, jockey_stats


# ── fit engineers the race context the classifier is trained on ───────────────


def test_fit_feeds_classifier_engineered_race_context() -> None:
    spy = _SpyAlgo()
    spy.fit(_rd(_make_train_df()))
    # fit_X is captured by the mock during fit (private spy attr, set non-None)
    cols = spy._mock.fit_X.columns  # pyright: ignore[reportPrivateUsage, reportOptionalMemberAccess]
    # HorseCount + the relative-rating column are materialised by the engine and
    # become features, alongside the required predictor and the raw extra feature.
    for expected in (_REQ_COL, "SomeRatingCol", "RelSomeRatingCol", "HorseCount"):
        assert expected in cols, f"{expected} not fed to the estimator"


# ── dropna: NaN in a required predictor drops the row before fitting ──────────


def test_fit_drops_rows_with_nan_required_predictor() -> None:
    spy = _SpyAlgo()
    rows = [
        _train_row(1, 10, wins=1),
        _train_row(1, 11, wins=0),
        _train_row(2, 20, wins=0, dist=None),  # NaN in required — dropped
    ]
    spy.fit(_rd(pd.DataFrame(rows)))
    assert len(spy._mock.fit_X) == 2  # pyright: ignore[reportPrivateUsage, reportArgumentType]


# ── extra_nan_tolerant_features column tolerates NaN in fit ───────────────────


def test_nan_in_extra_tolerant_feature_is_kept_nan_in_required_is_dropped() -> None:
    spy = _SpyAlgo()
    rows = [
        _train_row(1, 10, wins=1),
        _train_row(1, 11, wins=0),
        _train_row(2, 20, wins=0, some_rating=None),  # NaN in extra — should survive
        _train_row(2, 21, wins=1),
        _train_row(3, 30, wins=0, dist=None),  # NaN in required — should drop
    ]
    spy.fit(_rd(pd.DataFrame(rows)))

    # fit_X captured by the mock during fit (private spy attr, set non-None)
    assert len(spy._mock.fit_X) == 4  # pyright: ignore[reportPrivateUsage, reportArgumentType]  # horse 30 dropped; others kept
    assert "SomeRatingCol" in spy._mock.fit_X.columns  # pyright: ignore[reportPrivateUsage, reportOptionalMemberAccess]
    assert spy._mock.fit_X["SomeRatingCol"].isna().sum() == 1  # pyright: ignore[reportPrivateUsage, reportOptionalSubscript]  # horse 20's NaN survived


# ── the race gate runs after the complete-race filter, before scoring ─────────


def test_race_gate_sees_unscored_field_and_can_drop_it() -> None:
    class _GatedSpy(_SpyAlgo):
        def __init__(self) -> None:
            self._gate_frames: list[pd.DataFrame] = []
            super().__init__()

        def _race_gate(self, data: RaceData) -> RaceData:
            self._gate_frames.append(data.frame.copy())
            return data.subset(pd.Series(False, index=data.frame.index))

    spy = _GatedSpy()
    spy.fit(_rd(_make_train_df()))
    races, horse_stats, jockey_stats = _make_predict_fixtures()
    result = spy.predict_field(_serve(races, horse_stats, jockey_stats))

    assert result.empty  # gate dropped everything
    # _gate_frames records the frames the gate saw (private spy attr)
    assert len(spy._gate_frames) == 1  # pyright: ignore[reportPrivateUsage]
    assert "WinProbability" not in spy._gate_frames[0].columns  # pyright: ignore[reportPrivateUsage]  # gate runs pre-scoring


# ── predict_field() / predict() output shapes ─────────────────────────────────


def test_predict_field_returns_empty_before_fit() -> None:
    spy = _SpyAlgo()
    races, horse_stats, jockey_stats = _make_predict_fixtures()
    result = spy.predict_field(_serve(races, horse_stats, jockey_stats))
    assert result.empty


def test_predict_field_returns_all_horses_not_only_rank1() -> None:
    spy = _SpyAlgo()
    spy.fit(_rd(_make_train_df()))
    races, horse_stats, jockey_stats = _make_predict_fixtures(n_horses=3)
    result = spy.predict_field(_serve(races, horse_stats, jockey_stats))
    assert len(result) == 3, f"Expected 3 horses, got {len(result)}"
    assert set(result["HorseId"]) == {0, 1, 2}


def test_predict_field_has_win_probability_and_predicted_rank() -> None:
    spy = _SpyAlgo()
    spy.fit(_rd(_make_train_df()))
    races, horse_stats, jockey_stats = _make_predict_fixtures(n_horses=3)
    result = spy.predict_field(_serve(races, horse_stats, jockey_stats))
    assert "WinProbability" in result.columns
    assert "PredictedRank" in result.columns
    assert result["WinProbability"].notna().all()
    assert result["PredictedRank"].notna().all()


def test_predict_still_returns_only_rank1_pick() -> None:
    spy = _SpyAlgo()
    spy.fit(_rd(_make_train_df()))
    races, horse_stats, jockey_stats = _make_predict_fixtures(n_horses=3)
    preds = spy.predict(_serve(races, horse_stats, jockey_stats))
    assert len(preds) == 1
    assert list(preds.columns) == ["RaceId", "HorseId"]
