import pathlib
from datetime import date, timedelta
from typing import TYPE_CHECKING
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

if TYPE_CHECKING:
    from race_analytics.algorithms.confidence_gate import ConfidenceGate

from race_analytics.features.horse_stats import (
    extract_horse_stats as _compute_horse_stats,
)
from race_analytics.features.jockey_stats import (
    extract_jockey_stats as _compute_jockey_stats,
)
from race_analytics.features.race_data import RaceData
from race_analytics.features.race_history import race_card as _race_card
from race_analytics.scripts.evaluate import (
    _extract_known_races,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
)


class _FakeBuilder:
    """Stub RaceDataBuilder so evaluate()'s plumbing tests don't run real feature
    engineering on the minimal fold fixture. wrap_training/build_serving just wrap the
    frames into a RaceData.
    """

    def wrap_training(self, frame: pd.DataFrame, max_horses: int = 10) -> RaceData:
        return RaceData(
            frame.copy(),
            pd.Timestamp("2026-01-01"),  # pyright: ignore[reportArgumentType]  # Timestamp ctor return includes a NaTType arm
            max_horses,
        )

    def build_serving(
        self,
        card: pd.DataFrame,
        history: RaceData | pd.DataFrame,
        as_of: pd.Timestamp,
        max_horses: int = 10,
    ) -> RaceData:
        return RaceData(
            card.copy(),
            pd.Timestamp(as_of),  # pyright: ignore[reportArgumentType]  # Timestamp ctor return includes a NaTType arm
            max_horses,
        )


# ================================================================
# _extract_known_races
# ================================================================


def test_extract_known_races_removes_unknown_races() -> None:
    df = pd.DataFrame(
        [
            {"RaceId": 1, "HorseId": 10, "KnownHorseAndJockey": True},
            {"RaceId": 1, "HorseId": 11, "KnownHorseAndJockey": True},
            {"RaceId": 2, "HorseId": 20, "KnownHorseAndJockey": False},
            {"RaceId": 2, "HorseId": 21, "KnownHorseAndJockey": False},
        ]
    )
    result = _extract_known_races(df)
    assert set(result["RaceId"]) == {1}
    assert len(result) == 2


def test_extract_known_races_keeps_all_when_all_known() -> None:
    df = pd.DataFrame(
        [
            {"RaceId": 1, "HorseId": 10, "KnownHorseAndJockey": True},
            {"RaceId": 2, "HorseId": 20, "KnownHorseAndJockey": True},
        ]
    )
    result = _extract_known_races(df)
    assert len(result) == 2


def test_extract_known_races_returns_empty_when_none_known() -> None:
    df = pd.DataFrame(
        [
            {"RaceId": 1, "HorseId": 10, "KnownHorseAndJockey": False},
        ]
    )
    assert _extract_known_races(df).empty


# ================================================================
# _race_card — ratings flow only through the per-horse stats join
# ================================================================


def test_race_card_drops_rating_columns() -> None:
    fold_df = pd.DataFrame(
        [
            {
                "RaceId": 1,
                "HorseId": 10,
                "JockeyId": 100,
                "TrainerId": 1000,
                "Surface": "Turf",
                "Going": "Good",
                "RaceType": "Flat",
                "DistanceInMeters": 1600.0,
                "WeightInPounds": 126.0,
                "OfficialRating": 80.0,
                "RacingPostRating": 100.0,
                "TopSpeedRating": 90.0,
            }
        ]
    )
    card = _race_card(fold_df)
    for col in ["OfficialRating", "RacingPostRating", "TopSpeedRating"]:
        assert col not in card.columns, f"rating column leaked into the card: {col}"
    # essentials the algorithm re-encodes are still carried
    for col in ["RaceId", "HorseId", "JockeyId", "Surface", "Going", "RaceType"]:
        assert col in card.columns


# ================================================================
# Shared fixture helpers
# ================================================================


def _train_row(
    horse_id: int,
    jockey_id: int,
    off: str,
    finishing_pos: int = 2,
    horse_count: int = 5,
    speed: float = 15.0,
    dist: float = 1600.0,
    weight: float = 126.0,
    n_prior: float = 3.0,
    last_avg_rel_pos: float = 0.3,
    j_n_prior: float = 5.0,
    j_win_pct: float = 0.2,
    j_top3_pct: float = 0.4,
    j_avg_rel: float = 0.35,
) -> dict[str, object]:
    return {
        "HorseId": horse_id,
        "JockeyId": jockey_id,
        "Off": pd.Timestamp(off),
        "FinishingPosition": finishing_pos,
        "HorseCount": horse_count,
        "Speed": speed,
        "DistanceInMeters": dist,
        "WeightInPounds": weight,
        "NumberOfPriorRaces": n_prior,
        "LastRaceAvgRelFinishingPosition": last_avg_rel_pos,
        "JockeyNumberOfPriorRaces": j_n_prior,
        "JockeyWinPercentage": j_win_pct,
        "JockeyTop3Percentage": j_top3_pct,
        "JockeyAvgRelFinishingPosition": j_avg_rel,
        "Surface_AllWeather": 0.0,
        "Surface_Dirt": 0.0,
        "Surface_Turf": 1.0,
        "Going_Good": 1.0,
        "Going_Good_To_Soft": 0.0,
        "Going_Soft": 0.0,
        "Going_Good_To_Firm": 0.0,
        "Going_Firm": 0.0,
        "Going_Heavy": 0.0,
        "RaceType_Flat": 1.0,
        "RaceType_Hurdle": 0.0,
        "RaceType_Other": 0.0,
        "RaceType_SteepleChase": 0.0,
    }


# ================================================================
# _compute_horse_stats
# ================================================================


def test_horse_stats_one_row_per_horse() -> None:
    rows = [
        _train_row(horse_id=1, jockey_id=10, off="2026-01-01"),
        _train_row(horse_id=1, jockey_id=10, off="2026-02-01"),
        _train_row(horse_id=2, jockey_id=20, off="2026-01-15"),
    ]
    result = _compute_horse_stats(pd.DataFrame(rows))
    assert len(result) == 2
    assert set(result["HorseId"]) == {1, 2}


def test_horse_stats_uses_most_recent_race_as_last_off() -> None:
    rows = [
        _train_row(horse_id=1, jockey_id=10, off="2026-01-01", speed=14.0),
        _train_row(horse_id=1, jockey_id=10, off="2026-03-01", speed=16.0),
    ]
    result = _compute_horse_stats(pd.DataFrame(rows))
    row = result[result["HorseId"] == 1].iloc[0]
    assert row["LastOff"] == pd.Timestamp("2026-03-01")
    assert row["LastRaceSpeed"] == pytest.approx(16.0)


def test_horse_stats_has_required_columns() -> None:
    rows = [_train_row(horse_id=1, jockey_id=10, off="2026-01-01")]
    result = _compute_horse_stats(pd.DataFrame(rows))
    for col in [
        "HorseId",
        "LastOff",
        "LastRaceDistanceInMeters",
        "LastRaceWeightInPounds",
        "LastRaceSpeed",
        "LastRaceAvgRelFinishingPosition",
        "LastRaceSurface_Turf",
        "LastRaceGoing_Good",
        "LastRaceRaceType_Flat",
    ]:
        assert col in result.columns, f"Missing column: {col}"


def test_horse_stats_avg_rel_pos_incorporates_last_race() -> None:
    # n_prior=4, last_avg_rel_pos=0.4, finishing_pos=1, horse_count=5
    # updated = (0.4*4 + 1/5) / 5 = (1.6+0.2)/5 = 0.36
    rows = [
        _train_row(
            horse_id=1,
            jockey_id=10,
            off="2026-01-01",
            finishing_pos=1,
            horse_count=5,
            n_prior=4.0,
            last_avg_rel_pos=0.4,
        )
    ]
    result = _compute_horse_stats(pd.DataFrame(rows))
    assert result.iloc[0]["LastRaceAvgRelFinishingPosition"] == pytest.approx(0.36)


# ================================================================
# _compute_jockey_stats
# ================================================================


def test_jockey_stats_one_row_per_jockey() -> None:
    rows = [
        _train_row(horse_id=1, jockey_id=10, off="2026-01-01"),
        _train_row(horse_id=2, jockey_id=10, off="2026-02-01"),
        _train_row(horse_id=3, jockey_id=20, off="2026-01-15"),
    ]
    result = _compute_jockey_stats(pd.DataFrame(rows))
    assert len(result) == 2
    assert set(result["JockeyId"]) == {10, 20}


def test_jockey_stats_has_required_columns() -> None:
    rows = [_train_row(horse_id=1, jockey_id=10, off="2026-01-01")]
    result = _compute_jockey_stats(pd.DataFrame(rows))
    for col in [
        "JockeyId",
        "LastOff",
        "JockeyNumberOfPriorRaces",
        "JockeyWinPercentage",
        "JockeyTop3Percentage",
        "JockeyAvgRelFinishingPosition",
    ]:
        assert col in result.columns, f"Missing column: {col}"


def test_jockey_stats_excludes_jockey_id_zero() -> None:
    rows = [
        _train_row(horse_id=1, jockey_id=0, off="2026-01-01"),
        _train_row(horse_id=2, jockey_id=10, off="2026-01-01"),
    ]
    result = _compute_jockey_stats(pd.DataFrame(rows))
    assert 0 not in result["JockeyId"].values
    assert len(result) == 1


def test_jockey_stats_uses_most_recent_race_as_last_off() -> None:
    rows = [
        _train_row(horse_id=1, jockey_id=10, off="2026-01-01"),
        _train_row(horse_id=2, jockey_id=10, off="2026-03-01"),
    ]
    result = _compute_jockey_stats(pd.DataFrame(rows))
    assert result[result["JockeyId"] == 10].iloc[0]["LastOff"] == pd.Timestamp(
        "2026-03-01"
    )


# ================================================================
# _format_timing
# ================================================================


def test_format_timing_returns_pipe_prefixed_string() -> None:
    from race_analytics.scripts.evaluate import (
        _format_timing,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
    )

    assert _format_timing(1.234, 0.056) == "| fit=1.234s, predict=0.056s"


def test_format_timing_three_decimal_places() -> None:
    from race_analytics.scripts.evaluate import (
        _format_timing,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
    )

    result = _format_timing(0.1, 0.001)
    assert "fit=0.100s" in result
    assert "predict=0.001s" in result


# ================================================================
# _aggregate_times
# ================================================================


def test_aggregate_times_returns_mean_and_std() -> None:
    from race_analytics.scripts.evaluate import (
        _aggregate_times,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
    )

    # non-empty input always yields a (mean, std) tuple, never None
    mean, std = _aggregate_times([1.0, 2.0, 3.0])  # pyright: ignore[reportGeneralTypeIssues]  # result is non-None for non-empty input
    assert mean == pytest.approx(2.0)
    assert std == pytest.approx(np.std([1.0, 2.0, 3.0]))


def test_aggregate_times_single_value_has_zero_std() -> None:
    from race_analytics.scripts.evaluate import (
        _aggregate_times,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
    )

    # non-empty input always yields a (mean, std) tuple, never None
    mean, std = _aggregate_times([5.0])  # pyright: ignore[reportGeneralTypeIssues]  # result is non-None for non-empty input
    assert mean == pytest.approx(5.0)
    assert std == pytest.approx(0.0)


def test_aggregate_times_empty_returns_none() -> None:
    from race_analytics.scripts.evaluate import (
        _aggregate_times,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
    )

    assert _aggregate_times([]) is None


# ================================================================
# evaluate() — timing accumulation
# ================================================================


def _make_fold_races(fold_date: date) -> pd.DataFrame:
    """Minimal two-row DataFrame: one training row + one known fold row."""
    train_date = fold_date - timedelta(days=1)
    return pd.DataFrame(
        [
            {
                "Off": pd.Timestamp(train_date),
                "KnownHorseAndJockey": False,
                "RaceId": 1,
                "HorseId": 10,
                "JockeyId": 100,
                "TrainerId": 1000,
                "Surface": "Turf",
                "Going": "Good",
                "RaceType": "Flat",
                "DistanceInMeters": 1600.0,
                "WeightInPounds": 126.0,
                "FinishingPosition": 2,
                "DecimalOdds": 3.5,
                "ResultStatus": "CompletedRace",
                "HorseName": "TrainHorse",
                "CourseName": "Cheltenham",
            },
            {
                "Off": pd.Timestamp(fold_date),
                "KnownHorseAndJockey": True,
                "RaceId": 2,
                "HorseId": 20,
                "JockeyId": 200,
                "TrainerId": 2000,
                "Surface": "Turf",
                "Going": "Good",
                "RaceType": "Flat",
                "DistanceInMeters": 1600.0,
                "WeightInPounds": 126.0,
                "FinishingPosition": 1,
                "DecimalOdds": 3.5,
                "ResultStatus": "CompletedRace",
                "HorseName": "FoldHorse",
                "CourseName": "Ascot",
            },
        ]
    )


class _StubAlgo:
    """FieldPredictor stub. predict_field carries no WinProbability (regressor-like),
    so CSV WinProbability is NA — the post-migration analog of 'no predict_field'."""

    def __init__(self, max_horses: int = 10):
        self.max_horses = max_horses

    def fit(self, data: RaceData) -> None:
        pass

    def predict(self, data: RaceData) -> pd.DataFrame:
        frame = data.frame
        if frame.empty:
            return pd.DataFrame(columns=["RaceId", "HorseId"])
        return pd.DataFrame(
            [
                {
                    "RaceId": int(frame["RaceId"].iloc[0]),
                    "HorseId": int(frame["HorseId"].iloc[0]),
                }
            ]
        )

    def predict_field(self, data: RaceData) -> pd.DataFrame:
        frame = data.frame
        if frame.empty:
            return pd.DataFrame(columns=["RaceId", "HorseId", "PredictedRank"])
        return pd.DataFrame(
            [
                {
                    "RaceId": int(frame["RaceId"].iloc[0]),
                    "HorseId": int(frame["HorseId"].iloc[0]),
                    "PredictedRank": 1.0,
                }
            ]
        )


def test_evaluate_timing_summary_printed_after_accuracy_summary(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from race_analytics.scripts.evaluate import evaluate

    fold_date = date.today() - timedelta(days=1)
    stub_algo = _StubAlgo()

    with (
        patch(
            "race_analytics.scripts.evaluate._load_window",
            return_value=pd.DataFrame([{"x": 1}]),
        ),
        patch(
            "race_analytics.scripts.evaluate._engineer_features",
            return_value=_make_fold_races(fold_date),
        ),
        patch("race_analytics.scripts.evaluate.RaceDataBuilder", _FakeBuilder),
        patch("race_analytics.scripts.evaluate.ALGORITHMS", [stub_algo]),
    ):
        evaluate(folds=1)

    out = capsys.readouterr().out
    assert "=== Timing Summary ===" in out
    summary_pos = out.index("=== Summary ===")
    timing_pos = out.index("=== Timing Summary ===")
    assert timing_pos > summary_pos, "Timing summary must appear after accuracy summary"
    assert "Fit(avg)" in out
    assert "Pred(std)" in out


def test_evaluate_timing_summary_shows_na_for_skipped_algorithms(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from race_analytics.scripts.evaluate import evaluate

    # Return empty raw data so all folds are skipped (no known races)
    with (
        patch(
            "race_analytics.scripts.evaluate._load_window", return_value=pd.DataFrame()
        ),
        patch("race_analytics.scripts.evaluate.ALGORITHMS", [_StubAlgo()]),
    ):
        evaluate(folds=1)

    out = capsys.readouterr().out
    assert "=== Timing Summary ===" in out
    assert "N/A" in out


# ================================================================
# _roi_coverage_frontier
# ================================================================


def _make_field_preds(
    races_horses: list[tuple[int, list[tuple[int, float]]]],
) -> pd.DataFrame:
    """Build synthetic field-predictions DataFrame.
    races_horses: [(race_id, [(horse_id, win_prob), ...]), ...]
    PredictedRank=1 is assigned to the highest-probability horse per race.
    """
    rows = []
    for race_id, horses in races_horses:
        sorted_h = sorted(horses, key=lambda x: x[1], reverse=True)
        for rank, (horse_id, prob) in enumerate(sorted_h, start=1):
            rows.append(
                {
                    "RaceId": race_id,
                    "HorseId": horse_id,
                    "WinProbability": prob,
                    "PredictedRank": rank,
                }
            )
    return pd.DataFrame(rows)


def _make_results(picks: list[tuple[int, int, int, float]]) -> pd.DataFrame:
    """(race_id, horse_id, finishing_pos, decimal_odds)"""
    return pd.DataFrame(
        [
            {
                "RaceId": r,
                "HorseId": h,
                "FinishingPosition": p,
                "DecimalOdds": o,
                "ResultStatus": "CompletedRace",
            }
            for r, h, p, o in picks
        ]
    )


def test_roi_coverage_frontier_returns_expected_columns() -> None:
    from race_analytics.algorithms.confidence_gate import ConfidenceGate
    from race_analytics.scripts.evaluate import (
        _roi_coverage_frontier,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
    )

    gate = ConfidenceGate("top_prob")
    gate.calibrate([0.7, 0.6, 0.5, 0.4], coverage=1.0)

    field = _make_field_preds(
        [
            (1, [(10, 0.7), (11, 0.2), (12, 0.1)]),
            (2, [(20, 0.6), (21, 0.3), (22, 0.1)]),
        ]
    )
    results = _make_results(
        [
            (1, 10, 1, 3.0),
            (1, 11, 2, 5.0),
            (1, 12, 3, 2.0),
            (2, 20, 2, 4.0),
            (2, 21, 1, 6.0),
            (2, 22, 3, 2.0),
        ]
    )
    df = _roi_coverage_frontier(field, results, gate)
    assert set(df.columns) >= {"coverage_target", "actual_coverage", "roi", "races"}


def test_roi_coverage_frontier_full_coverage_keeps_all_races() -> None:
    from race_analytics.algorithms.confidence_gate import ConfidenceGate
    from race_analytics.scripts.evaluate import (
        _roi_coverage_frontier,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
    )

    gate = ConfidenceGate("top_prob")
    gate.calibrate([0.5, 0.6, 0.7, 0.8], coverage=1.0)

    field = _make_field_preds(
        [
            (1, [(10, 0.8), (11, 0.2)]),
            (2, [(20, 0.6), (21, 0.4)]),
            (3, [(30, 0.5), (31, 0.5)]),
        ]
    )
    results = _make_results(
        [
            (1, 10, 1, 3.0),
            (1, 11, 2, 2.0),
            (2, 20, 2, 4.0),
            (2, 21, 1, 5.0),
            (3, 30, 1, 2.0),
            (3, 31, 2, 3.0),
        ]
    )
    df = _roi_coverage_frontier(field, results, gate, coverages=[1.0])
    row = df[df["coverage_target"] == 1.0].iloc[0]
    assert row["races"] == 3


def test_roi_coverage_frontier_tighter_coverage_fewer_races() -> None:
    from race_analytics.algorithms.confidence_gate import ConfidenceGate
    from race_analytics.scripts.evaluate import (
        _roi_coverage_frontier,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
    )

    gate = ConfidenceGate("top_prob")
    gate.calibrate([0.5, 0.6, 0.7, 0.8], coverage=1.0)

    field = _make_field_preds(
        [
            (1, [(10, 0.8), (11, 0.2)]),
            (2, [(20, 0.6), (21, 0.4)]),
            (3, [(30, 0.5), (31, 0.5)]),
            (4, [(40, 0.4), (41, 0.6)]),
        ]
    )
    results = _make_results(
        [
            (1, 10, 1, 3.0),
            (1, 11, 2, 2.0),
            (2, 20, 2, 4.0),
            (2, 21, 1, 5.0),
            (3, 30, 1, 2.0),
            (3, 31, 2, 3.0),
            (4, 40, 2, 2.0),
            (4, 41, 1, 3.0),
        ]
    )
    df = _roi_coverage_frontier(field, results, gate, coverages=[1.0, 0.5])
    races_full = df[df["coverage_target"] == 1.0]["races"].iloc[0]  # pyright: ignore[reportAttributeAccessIssue]  # column select yields a Series with .iloc
    races_tight = df[df["coverage_target"] == 0.5]["races"].iloc[0]  # pyright: ignore[reportAttributeAccessIssue]  # column select yields a Series with .iloc
    assert races_tight <= races_full


# ================================================================
# _print_early_late_split — structural smoke test
# ================================================================


def test_early_late_split_printed_in_evaluate_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from race_analytics.scripts.evaluate import evaluate

    fold_date = date.today() - timedelta(days=1)
    stub_algo = _StubAlgo()

    with (
        patch(
            "race_analytics.scripts.evaluate._load_window",
            return_value=pd.DataFrame([{"x": 1}]),
        ),
        patch(
            "race_analytics.scripts.evaluate._engineer_features",
            return_value=_make_fold_races(fold_date),
        ),
        patch("race_analytics.scripts.evaluate.RaceDataBuilder", _FakeBuilder),
        patch("race_analytics.scripts.evaluate.ALGORITHMS", [stub_algo]),
    ):
        evaluate(folds=1)

    out = capsys.readouterr().out
    assert "=== Early-vs-Late Stability ===" in out


# ================================================================
# _build_csv_rows
# ================================================================

_CSV_COLUMNS = [
    "FoldDate",
    "Algorithm",
    "RaceId",
    "HorseId",
    "CourseName",
    "Surface",
    "Going",
    "RaceType",
    "DistanceInMeters",
    "FinishingPosition",
    "DecimalOdds",
    "PredictedScore",
    "WinProbability",
    "FieldSize",
    "RaceClass",
]


def _minimal_preds(race_id: int = 2, horse_id: int = 20) -> pd.DataFrame:
    return pd.DataFrame([{"RaceId": race_id, "HorseId": horse_id}])


def _minimal_known_fold(race_id: int = 2, horse_id: int = 20) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "RaceId": race_id,
                "HorseId": horse_id,
                "CourseName": "Ascot",
                "Surface": "Turf",
                "Going": "Good",
                "RaceType": "Flat",
                "DistanceInMeters": 1600.0,
            }
        ]
    )


def _minimal_results(race_id: int = 2, horse_id: int = 20) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "RaceId": race_id,
                "HorseId": horse_id,
                "FinishingPosition": 1,
                "DecimalOdds": 3.5,
                "ResultStatus": "CompletedRace",
            }
        ]
    )


def test_build_csv_rows_has_required_columns() -> None:
    from race_analytics.scripts.evaluate import (
        _build_csv_rows,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
    )

    rows = _build_csv_rows(
        date(2026, 5, 29),
        "_StubAlgo",
        _minimal_preds(),
        _minimal_known_fold(),
        _minimal_results(),
    )
    assert list(rows.columns) == _CSV_COLUMNS


def test_build_csv_rows_surface_going_racetype_are_raw_strings() -> None:
    from race_analytics.scripts.evaluate import (
        _build_csv_rows,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
    )

    rows = _build_csv_rows(
        date(2026, 5, 29),
        "_StubAlgo",
        _minimal_preds(),
        _minimal_known_fold(),
        _minimal_results(),
    )
    assert rows.iloc[0]["Surface"] == "Turf"
    assert rows.iloc[0]["Going"] == "Good"
    assert rows.iloc[0]["RaceType"] == "Flat"


def test_build_csv_rows_predicted_score_from_predicted_speed() -> None:
    from race_analytics.scripts.evaluate import (
        _build_csv_rows,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
    )

    preds = pd.DataFrame([{"RaceId": 2, "HorseId": 20, "PredictedSpeed": 17.5}])
    rows = _build_csv_rows(
        date(2026, 5, 29),
        "_StubAlgo",
        preds,
        _minimal_known_fold(),
        _minimal_results(),
    )
    assert rows.iloc[0]["PredictedScore"] == pytest.approx(17.5)


def test_build_csv_rows_predicted_score_null_when_no_predicted_speed() -> None:
    from race_analytics.scripts.evaluate import (
        _build_csv_rows,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
    )

    rows = _build_csv_rows(
        date(2026, 5, 29),
        "_StubAlgo",
        _minimal_preds(),
        _minimal_known_fold(),
        _minimal_results(),
    )
    assert pd.isna(rows.iloc[0]["PredictedScore"])


def test_build_csv_rows_empty_preds_returns_empty_frame() -> None:
    from race_analytics.scripts.evaluate import (
        _build_csv_rows,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
    )

    rows = _build_csv_rows(
        date(2026, 5, 29),
        "_StubAlgo",
        pd.DataFrame(columns=["RaceId", "HorseId"]),
        _minimal_known_fold(),
        _minimal_results(),
    )
    assert rows.empty
    assert list(rows.columns) == _CSV_COLUMNS


def test_build_csv_rows_carries_win_probability_when_present() -> None:
    from race_analytics.scripts.evaluate import (
        _build_csv_rows,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
    )

    preds = pd.DataFrame([{"RaceId": 2, "HorseId": 20, "WinProbability": 0.42}])
    rows = _build_csv_rows(
        date(2026, 5, 29),
        "_StubAlgo",
        preds,
        _minimal_known_fold(),
        _minimal_results(),
    )
    assert rows.iloc[0]["WinProbability"] == pytest.approx(0.42)


def test_build_csv_rows_win_probability_na_when_absent() -> None:
    from race_analytics.scripts.evaluate import (
        _build_csv_rows,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
    )

    rows = _build_csv_rows(
        date(2026, 5, 29),
        "_StubAlgo",
        _minimal_preds(),
        _minimal_known_fold(),
        _minimal_results(),
    )
    assert pd.isna(rows.iloc[0]["WinProbability"])


def test_build_csv_rows_field_size_equals_horses_in_race() -> None:
    from race_analytics.scripts.evaluate import (
        _build_csv_rows,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
    )

    known_fold = pd.DataFrame(
        [
            {
                "RaceId": 2,
                "HorseId": 20,
                "CourseName": "Ascot",
                "Surface": "Turf",
                "Going": "Good",
                "RaceType": "Flat",
                "DistanceInMeters": 1600.0,
            },
            {
                "RaceId": 2,
                "HorseId": 21,
                "CourseName": "Ascot",
                "Surface": "Turf",
                "Going": "Good",
                "RaceType": "Flat",
                "DistanceInMeters": 1600.0,
            },
            {
                "RaceId": 2,
                "HorseId": 22,
                "CourseName": "Ascot",
                "Surface": "Turf",
                "Going": "Good",
                "RaceType": "Flat",
                "DistanceInMeters": 1600.0,
            },
            {
                "RaceId": 2,
                "HorseId": 23,
                "CourseName": "Ascot",
                "Surface": "Turf",
                "Going": "Good",
                "RaceType": "Flat",
                "DistanceInMeters": 1600.0,
            },
        ]
    )
    results = pd.DataFrame(
        [
            {
                "RaceId": 2,
                "HorseId": 20,
                "FinishingPosition": 1,
                "DecimalOdds": 3.5,
                "ResultStatus": "CompletedRace",
            },
        ]
    )
    rows = _build_csv_rows(
        date(2026, 5, 29),
        "_StubAlgo",
        _minimal_preds(),
        known_fold,
        results,
    )
    assert rows.iloc[0]["FieldSize"] == 4


def test_build_csv_rows_race_class_from_class_column() -> None:
    from race_analytics.scripts.evaluate import (
        _build_csv_rows,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
    )

    known_fold = pd.DataFrame(
        [
            {
                "RaceId": 2,
                "HorseId": 20,
                "CourseName": "Ascot",
                "Surface": "Turf",
                "Going": "Good",
                "RaceType": "Flat",
                "DistanceInMeters": 1600.0,
                "Class": "Class 3",
            }
        ]
    )
    rows = _build_csv_rows(
        date(2026, 5, 29),
        "_StubAlgo",
        _minimal_preds(),
        known_fold,
        _minimal_results(),
    )
    assert rows.iloc[0]["RaceClass"] == "Class 3"


def test_build_csv_rows_race_class_na_when_no_class_column() -> None:
    from race_analytics.scripts.evaluate import (
        _build_csv_rows,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
    )

    rows = _build_csv_rows(
        date(2026, 5, 29),
        "_StubAlgo",
        _minimal_preds(),
        _minimal_known_fold(),
        _minimal_results(),
    )
    assert pd.isna(rows.iloc[0]["RaceClass"])


# ================================================================
# evaluate() — predict_field() integration
# ================================================================


class _FieldAlgo:
    """FieldPredictor stub whose predict_field returns per-horse WinProbability."""

    def __init__(self, max_horses: int = 10):
        self.max_horses = max_horses

    def fit(self, data: RaceData) -> None:
        pass

    def predict(self, data: RaceData) -> pd.DataFrame:
        frame = data.frame
        if frame.empty:
            return pd.DataFrame(columns=["RaceId", "HorseId"])
        return pd.DataFrame(
            [
                {
                    "RaceId": int(frame["RaceId"].iloc[0]),
                    "HorseId": int(frame["HorseId"].iloc[0]),
                }
            ]
        )

    def predict_field(self, data: RaceData) -> pd.DataFrame:
        frame = data.frame
        if frame.empty:
            return pd.DataFrame(
                columns=["RaceId", "HorseId", "WinProbability", "PredictedRank"]
            )
        return pd.DataFrame(
            [
                {
                    "RaceId": int(frame["RaceId"].iloc[0]),
                    "HorseId": int(frame["HorseId"].iloc[0]),
                    "WinProbability": 0.75,
                    "PredictedRank": 1.0,
                }
            ]
        )


def test_evaluate_csv_carries_win_probability_for_predict_field_algo(
    tmp_path: pathlib.Path,
) -> None:
    from race_analytics.scripts.evaluate import evaluate

    fold_date = date.today() - timedelta(days=1)
    out_path = str(tmp_path / "results.csv")
    with (
        patch(
            "race_analytics.scripts.evaluate._load_window",
            return_value=pd.DataFrame([{"x": 1}]),
        ),
        patch(
            "race_analytics.scripts.evaluate._engineer_features",
            return_value=_make_fold_races(fold_date),
        ),
        patch("race_analytics.scripts.evaluate.RaceDataBuilder", _FakeBuilder),
        patch("race_analytics.scripts.evaluate.ALGORITHMS", [_FieldAlgo()]),
    ):
        evaluate(folds=1, save_results=True, results_file=out_path)
    df = pd.read_csv(out_path)
    assert df.iloc[0]["WinProbability"] == pytest.approx(0.75)


def test_evaluate_csv_win_probability_na_for_non_field_algo(
    tmp_path: pathlib.Path,
) -> None:
    from race_analytics.scripts.evaluate import evaluate

    fold_date = date.today() - timedelta(days=1)
    out_path = str(tmp_path / "results.csv")
    with (
        patch(
            "race_analytics.scripts.evaluate._load_window",
            return_value=pd.DataFrame([{"x": 1}]),
        ),
        patch(
            "race_analytics.scripts.evaluate._engineer_features",
            return_value=_make_fold_races(fold_date),
        ),
        patch("race_analytics.scripts.evaluate.RaceDataBuilder", _FakeBuilder),
        patch("race_analytics.scripts.evaluate.ALGORITHMS", [_StubAlgo()]),
    ):
        evaluate(folds=1, save_results=True, results_file=out_path)
    df = pd.read_csv(out_path)
    assert df["WinProbability"].isna().all()


# ================================================================
# evaluate() — the declared FieldPredictor / AbstainCapable contract
# (no hasattr/getattr/type() probing of algorithms)
# ================================================================


class _AbstainAlgo(_FieldAlgo):
    """FieldPredictor + AbstainCapable. The harness must detect abstention via the
    AbstainCapable Protocol (isinstance), not by probing for method names."""

    def __init__(self, max_horses: int = 10):
        super().__init__(max_horses)
        from race_analytics.algorithms.confidence_gate import ConfidenceGate

        self._gate = ConfidenceGate("top_prob")
        self._gate.calibrate([0.5, 0.6, 0.7, 0.8], coverage=1.0)

    def predict_field_unfiltered(self, data: RaceData) -> pd.DataFrame:
        return self.predict_field(data)

    def get_confidence_gate(self) -> "ConfidenceGate | None":
        return self._gate


def test_plain_field_predictor_is_not_abstain_capable() -> None:
    from race_analytics.algorithms.base import AbstainCapable, FieldPredictor

    assert isinstance(_FieldAlgo(), FieldPredictor)
    assert not isinstance(_FieldAlgo(), AbstainCapable)
    assert isinstance(_AbstainAlgo(), AbstainCapable)


def test_evaluate_runs_field_predictor_with_no_frontier(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A plain FieldPredictor (not abstain-capable) runs through the contract and
    produces no ROI-vs-coverage frontier — the harness never probes for the methods."""
    from race_analytics.scripts.evaluate import evaluate

    fold_date = date.today() - timedelta(days=1)
    with (
        patch(
            "race_analytics.scripts.evaluate._load_window",
            return_value=pd.DataFrame([{"x": 1}]),
        ),
        patch(
            "race_analytics.scripts.evaluate._engineer_features",
            return_value=_make_fold_races(fold_date),
        ),
        patch("race_analytics.scripts.evaluate.RaceDataBuilder", _FakeBuilder),
        patch("race_analytics.scripts.evaluate.ALGORITHMS", [_FieldAlgo()]),
    ):
        evaluate(folds=1)
    out = capsys.readouterr().out
    assert "ROI-vs-Coverage Frontier" not in out


def test_evaluate_abstain_capable_algo_triggers_frontier(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An AbstainCapable algorithm's unfiltered field + gate drive the frontier,
    selected via isinstance(algo, AbstainCapable)."""
    from race_analytics.scripts.evaluate import evaluate

    fold_date = date.today() - timedelta(days=1)
    with (
        patch(
            "race_analytics.scripts.evaluate._load_window",
            return_value=pd.DataFrame([{"x": 1}]),
        ),
        patch(
            "race_analytics.scripts.evaluate._engineer_features",
            return_value=_make_fold_races(fold_date),
        ),
        patch("race_analytics.scripts.evaluate.RaceDataBuilder", _FakeBuilder),
        patch("race_analytics.scripts.evaluate.ALGORITHMS", [_AbstainAlgo()]),
    ):
        evaluate(folds=1)
    out = capsys.readouterr().out
    assert "=== ROI-vs-Coverage Frontier: _AbstainAlgo ===" in out


# ================================================================
# evaluate() — full real path (real RaceDataBuilder + real algorithm)
# ================================================================


def _enriched_fold_frame(fold_date: date) -> pd.DataFrame:
    """A complete `_engineer_features`-shaped frame: two training flat races (horse 0
    wins) plus one fold race of three known horses. Rich enough for the real
    RaceDataBuilder (extract_*_stats + canonical chain) and a real classifier."""
    base = {
        "Surface": "Turf",
        "Going": "Good",
        "RaceType": "Flat",
        "Surface_AllWeather": 0.0,
        "Surface_Dirt": 0.0,
        "Surface_Turf": 1.0,
        "Going_Good": 1.0,
        "Going_Good_To_Soft": 0.0,
        "Going_Soft": 0.0,
        "Going_Good_To_Firm": 0.0,
        "Going_Firm": 0.0,
        "Going_Heavy": 0.0,
        "RaceType_Flat": 1.0,
        "RaceType_Hurdle": 0.0,
        "RaceType_Other": 0.0,
        "RaceType_SteepleChase": 0.0,
        "DistanceInMeters": 1600.0,
        "WeightInPounds": 126.0,
        "Class": "3",
        "Age": 4,
        "Pattern": "",
        "RatingBand": "0-100",
        "AgeBand": "3yo+",
        "SexRestriction": "",
        "HeadGear": "",
        "OfficialRating": 80.0,
        "RacingPostRating": 100.0,
        "TopSpeedRating": 90.0,
        "NumberOfPriorRaces": 5.0,
        "LastRaceAvgRelFinishingPosition": 0.4,
        "DaysRested": 7.0,
        "DaysSinceJockeyLastRaced": 3.0,
        "JockeyNumberOfPriorRaces": 10.0,
        "JockeyWinPercentage": 0.2,
        "JockeyTop3Percentage": 0.5,
        "JockeyAvgRelFinishingPosition": 0.4,
        "TrainerNumberOfPriorRaces": 20.0,
        "TrainerWinPercentage": 0.15,
        "TrainerTop3Percentage": 0.45,
        "TrainerAvgRelFinishingPosition": 0.42,
        "LastRaceDistanceInMeters": 1600.0,
        "LastRaceWeightInPounds": 126.0,
        "LastRaceSpeed": 15.5,
        "LastRaceSurface_AllWeather": 0.0,
        "LastRaceSurface_Dirt": 0.0,
        "LastRaceSurface_Turf": 1.0,
        "LastRaceGoing_Good": 1.0,
        "LastRaceGoing_Good_To_Soft": 0.0,
        "LastRaceGoing_Soft": 0.0,
        "LastRaceGoing_Good_To_Firm": 0.0,
        "LastRaceGoing_Firm": 0.0,
        "LastRaceGoing_Heavy": 0.0,
        "LastRaceRaceType_Flat": 1.0,
        "LastRaceRaceType_Hurdle": 0.0,
        "LastRaceRaceType_Other": 0.0,
        "LastRaceRaceType_SteepleChase": 0.0,
        "Last3RaceAvgSpeed": np.nan,
        "Last3RaceSpeedTrend": np.nan,
        "Last3AvgRelFinishingPosition": np.nan,
        "ResultStatus": "CompletedRace",
    }
    rows = []
    for r in (1, 2):
        for h in range(4):
            hid = r * 10 + h
            rows.append(
                {
                    **base,
                    "RaceId": r,
                    "HorseId": hid,
                    "JockeyId": 100 + hid,
                    "TrainerId": 1000 + hid,
                    "Off": pd.Timestamp("2026-05-10 13:00:00"),
                    "KnownHorseAndJockey": False,
                    "StallNumber": h + 1,
                    "FinishingPosition": h + 1,
                    "HorseCount": 4,
                    "Speed": 16.0 - h * 0.1,
                    "Wins": 1 if h == 0 else 0,
                    "DecimalOdds": 3.0 + h,
                    "CourseName": "Ascot",
                    "HorseName": f"H{hid}",
                }
            )
    for h, hid in enumerate([10, 11, 20]):
        rows.append(
            {
                **base,
                "RaceId": 99,
                "HorseId": hid,
                "JockeyId": 100 + hid,
                "TrainerId": 1000 + hid,
                "Off": pd.Timestamp(f"{fold_date} 14:30:00"),
                "KnownHorseAndJockey": True,
                "StallNumber": h + 1,
                "FinishingPosition": h + 1,
                "HorseCount": 3,
                "Speed": 16.0,
                "Wins": 1 if h == 0 else 0,
                "DecimalOdds": 3.5,
                "CourseName": "York",
                "HorseName": f"H{hid}",
            }
        )
    return pd.DataFrame(rows)


def test_evaluate_end_to_end_with_real_builder_and_active_algorithm(
    tmp_path: pathlib.Path,
) -> None:
    """Drive evaluate() through the real RaceDataBuilder and the real ACTIVE algorithm
    (GatedRecencyWeightedWinClassifier) — exercising wrap_training + build_serving +
    fit/predict/predict_field/predict_field_unfiltered + the gate, end to end."""
    from race_analytics.algorithms import GatedRecencyWeightedWinClassifier
    from race_analytics.scripts.evaluate import evaluate

    fold_date = date(2026, 5, 20)
    out_path = str(tmp_path / "results.csv")
    with (
        patch("race_analytics.scripts.evaluate._fold_dates", return_value=[fold_date]),
        patch(
            "race_analytics.scripts.evaluate._load_window",
            return_value=pd.DataFrame([{"x": 1}]),
        ),
        patch(
            "race_analytics.scripts.evaluate._engineer_features",
            return_value=_enriched_fold_frame(fold_date),
        ),
        patch(
            "race_analytics.scripts.evaluate.ALGORITHMS",
            [GatedRecencyWeightedWinClassifier(max_horses=10)],
        ),
    ):
        evaluate(folds=1, save_results=True, results_file=out_path)

    df = pd.read_csv(out_path)
    assert not df.empty
    assert (df["Algorithm"] == "GatedRecencyWeightedWinClassifier").all()
    assert set(df["RaceId"]) == {99}
    assert (
        df["WinProbability"].notna().all()
    )  # the gated win-classifier carries probabilities


# ================================================================
# evaluate() — CSV export
# ================================================================


def test_evaluate_no_flags_writes_no_file(tmp_path: pathlib.Path) -> None:
    from race_analytics.scripts.evaluate import evaluate

    with patch(
        "race_analytics.scripts.evaluate._load_window", return_value=pd.DataFrame()
    ):
        evaluate(folds=1)
    assert list(tmp_path.iterdir()) == []


def test_evaluate_save_results_writes_csv_with_correct_schema(
    tmp_path: pathlib.Path,
) -> None:
    from race_analytics.scripts.evaluate import evaluate

    fold_date = date.today() - timedelta(days=1)
    out_path = str(tmp_path / "results.csv")
    with (
        patch(
            "race_analytics.scripts.evaluate._load_window",
            return_value=pd.DataFrame([{"x": 1}]),
        ),
        patch(
            "race_analytics.scripts.evaluate._engineer_features",
            return_value=_make_fold_races(fold_date),
        ),
        patch("race_analytics.scripts.evaluate.RaceDataBuilder", _FakeBuilder),
        patch("race_analytics.scripts.evaluate.ALGORITHMS", [_StubAlgo()]),
    ):
        evaluate(folds=1, save_results=True, results_file=out_path)
    df = pd.read_csv(out_path)
    assert list(df.columns) == _CSV_COLUMNS


def test_evaluate_results_file_without_save_results_still_writes(
    tmp_path: pathlib.Path,
) -> None:
    from race_analytics.scripts.evaluate import evaluate

    fold_date = date.today() - timedelta(days=1)
    out_path = str(tmp_path / "results.csv")
    with (
        patch(
            "race_analytics.scripts.evaluate._load_window",
            return_value=pd.DataFrame([{"x": 1}]),
        ),
        patch(
            "race_analytics.scripts.evaluate._engineer_features",
            return_value=_make_fold_races(fold_date),
        ),
        patch("race_analytics.scripts.evaluate.RaceDataBuilder", _FakeBuilder),
        patch("race_analytics.scripts.evaluate.ALGORITHMS", [_StubAlgo()]),
    ):
        evaluate(folds=1, results_file=out_path)
    assert (tmp_path / "results.csv").exists()


def test_evaluate_timing_accumulators_have_one_entry_per_completed_fold() -> None:
    from race_analytics.scripts.evaluate import evaluate

    fold_date = date.today() - timedelta(days=1)
    stub_algo = _StubAlgo()

    with (
        patch(
            "race_analytics.scripts.evaluate._load_window",
            return_value=pd.DataFrame([{"x": 1}]),
        ),
        patch(
            "race_analytics.scripts.evaluate._engineer_features",
            return_value=_make_fold_races(fold_date),
        ),
        patch("race_analytics.scripts.evaluate.RaceDataBuilder", _FakeBuilder),
        patch("race_analytics.scripts.evaluate.ALGORITHMS", [stub_algo]),
    ):
        timing = evaluate(folds=1)

    name = "_StubAlgo"
    assert name in timing["fit_times"], (
        f"Expected '{name}' key; got {list(timing['fit_times'])}"
    )
    assert len(timing["fit_times"][name]) == 1
    assert len(timing["predict_times"][name]) == 1
    assert timing["fit_times"][name][0] >= 0.0
    assert timing["predict_times"][name][0] >= 0.0


def test_evaluate_with_zero_folds_returns_without_unbound_error() -> None:
    """evaluate(folds=0) must not crash referencing `selected_algos` unbound.

    Regression: `selected_algos` was assigned only inside the per-fold loop, so a
    zero-fold run reached the ROI-vs-coverage frontier with it unbound (NameError).
    It is now initialised before the loop and the frontier guards missing entries.
    """
    from race_analytics.scripts.evaluate import evaluate

    result = evaluate(folds=0)

    assert isinstance(result, dict)


# ================================================================
# _engineer_features — MarketProb materialized on the training path
# (PRD: "Materialize in two non-shared places" — place (a))
# ================================================================


def _raw_results_frame() -> pd.DataFrame:
    """A minimal `Results_*.csv`-shaped frame (the input to `_engineer_features`).

    Two runners in one race on a single day. Carries the SP (DecimalOdds) and a
    forward-merged forecast (ForecastDecimalOdds) on the favourite only, so the
    resolver's forecast-then-SP coalesce is exercised. Single-day, so the per-day
    stats processors leave their columns at defaults — MarketProb depends only on the
    odds columns, so the engineered stats are irrelevant to it."""
    base = {
        "CourseId": 1,
        "CourseName": "Ascot",
        "RaceType": "Flat",
        "Class": "3",
        "OfficialRating": 80.0,
        "RacingPostRating": 100.0,
        "TopSpeedRating": 90.0,
        "DistanceInMeters": 1600.0,
        "Going": "Good",
        "Surface": "Turf",
        "Age": 4,
        "HeadGear": "",
        "WeightInPounds": 126.0,
        "Pattern": "",
        "RatingBand": "0-100",
        "AgeBand": "3yo+",
        "SexRestriction": "",
        "OverallBeatenDistance": 1.0,
        "RaceTimeInSeconds": 100.0,
        "ResultStatus": "CompletedRace",
        "Off": pd.Timestamp("2026-05-10 14:30:00"),
    }
    return pd.DataFrame(
        [
            {
                **base,
                "RaceId": 1,
                "HorseId": 10,
                "HorseName": "H10",
                "JockeyId": 100,
                "JockeyName": "J100",
                "TrainerId": 1000,
                "TrainerName": "T1000",
                "RaceCardNumber": 1,
                "StallNumber": 1,
                "FinishingPosition": 1,
                "DecimalOdds": 3.0,
                "ForecastDecimalOdds": 2.0,  # forecast present -> preferred over SP
            },
            {
                **base,
                "RaceId": 1,
                "HorseId": 11,
                "HorseName": "H11",
                "JockeyId": 101,
                "JockeyName": "J101",
                "TrainerId": 1001,
                "TrainerName": "T1001",
                "RaceCardNumber": 2,
                "StallNumber": 2,
                "FinishingPosition": 2,
                "DecimalOdds": 4.0,
                "ForecastDecimalOdds": float("nan"),  # no forecast -> SP fallback
            },
        ]
    )


def test_keep_cols_includes_forecast_decimal_odds() -> None:
    from race_analytics.scripts.evaluate import (
        _KEEP_COLS,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal constant
    )

    assert "ForecastDecimalOdds" in _KEEP_COLS
    # The SP column is still carried alongside it (the resolver's fallback input).
    assert "DecimalOdds" in _KEEP_COLS


def test_engineer_features_materializes_dense_market_prob() -> None:
    from race_analytics.scripts.evaluate import (
        _engineer_features,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
    )

    engineered = _engineer_features(_raw_results_frame())
    assert "MarketProb" in engineered.columns
    assert engineered["MarketProb"].notna().all()
    for _, race in engineered.groupby("RaceId"):
        assert race["MarketProb"].sum() == pytest.approx(1.0)


def test_market_prob_parity_between_training_and_serving_paths() -> None:
    """A runner's MarketProb is identical whether materialized via the harness
    training path (`_engineer_features`) or the canonical serving transform
    (`calculate_market_prob`), so the documented two-place materialization can't drift.
    """
    from race_analytics.features.transforms import calculate_market_prob
    from race_analytics.scripts.evaluate import (
        _engineer_features,  # pyright: ignore[reportPrivateUsage]  # intentional: testing module-internal helper
    )

    raw = _raw_results_frame()

    # Training path: full in-memory feature engineering.
    train = _engineer_features(raw)[["RaceId", "HorseId", "MarketProb"]]

    # Serving path: the canonical-chain transform on the equivalent odds input.
    serve = calculate_market_prob(
        raw[["RaceId", "HorseId", "DecimalOdds", "ForecastDecimalOdds"]].copy()
    )[["RaceId", "HorseId", "MarketProb"]]

    merged = train.merge(serve, on=["RaceId", "HorseId"], suffixes=("_train", "_serve"))
    assert len(merged) == len(raw)
    assert merged["MarketProb_train"].tolist() == pytest.approx(
        merged["MarketProb_serve"].tolist()
    )
