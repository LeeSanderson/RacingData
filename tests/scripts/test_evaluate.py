import pandas as pd
import numpy as np
import pytest
from datetime import date, timedelta
from unittest.mock import patch

from race_analytics.scripts.evaluate import _extract_known_races, _race_card
from race_analytics.features.horse_stats import extract_horse_stats as _compute_horse_stats
from race_analytics.features.jockey_stats import extract_jockey_stats as _compute_jockey_stats


# ================================================================
# _extract_known_races
# ================================================================

def test_extract_known_races_removes_unknown_races():
    df = pd.DataFrame([
        {"RaceId": 1, "HorseId": 10, "KnownHorseAndJockey": True},
        {"RaceId": 1, "HorseId": 11, "KnownHorseAndJockey": True},
        {"RaceId": 2, "HorseId": 20, "KnownHorseAndJockey": False},
        {"RaceId": 2, "HorseId": 21, "KnownHorseAndJockey": False},
    ])
    result = _extract_known_races(df)
    assert set(result["RaceId"]) == {1}
    assert len(result) == 2


def test_extract_known_races_keeps_all_when_all_known():
    df = pd.DataFrame([
        {"RaceId": 1, "HorseId": 10, "KnownHorseAndJockey": True},
        {"RaceId": 2, "HorseId": 20, "KnownHorseAndJockey": True},
    ])
    result = _extract_known_races(df)
    assert len(result) == 2


def test_extract_known_races_returns_empty_when_none_known():
    df = pd.DataFrame([
        {"RaceId": 1, "HorseId": 10, "KnownHorseAndJockey": False},
    ])
    assert _extract_known_races(df).empty


# ================================================================
# _race_card — ratings flow only through the per-horse stats join
# ================================================================

def test_race_card_drops_rating_columns():
    fold_df = pd.DataFrame([{
        "RaceId": 1, "HorseId": 10, "JockeyId": 100, "TrainerId": 1000,
        "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
        "DistanceInMeters": 1600.0, "WeightInPounds": 126.0,
        "OfficialRating": 80.0, "RacingPostRating": 100.0, "TopSpeedRating": 90.0,
    }])
    card = _race_card(fold_df)
    for col in ["OfficialRating", "RacingPostRating", "TopSpeedRating"]:
        assert col not in card.columns, f"rating column leaked into the card: {col}"
    # essentials the algorithm re-encodes are still carried
    for col in ["RaceId", "HorseId", "JockeyId", "Surface", "Going", "RaceType"]:
        assert col in card.columns


# ================================================================
# Shared fixture helpers
# ================================================================

def _train_row(horse_id, jockey_id, off, finishing_pos=2, horse_count=5,
               speed=15.0, dist=1600.0, weight=126.0,
               n_prior=3.0, last_avg_rel_pos=0.3,
               j_n_prior=5.0, j_win_pct=0.2, j_top3_pct=0.4, j_avg_rel=0.35):
    return {
        "HorseId": horse_id, "JockeyId": jockey_id,
        "Off": pd.Timestamp(off),
        "FinishingPosition": finishing_pos, "HorseCount": horse_count,
        "Speed": speed, "DistanceInMeters": dist, "WeightInPounds": weight,
        "NumberOfPriorRaces": n_prior,
        "LastRaceAvgRelFinishingPosition": last_avg_rel_pos,
        "JockeyNumberOfPriorRaces": j_n_prior,
        "JockeyWinPercentage": j_win_pct,
        "JockeyTop3Percentage": j_top3_pct,
        "JockeyAvgRelFinishingPosition": j_avg_rel,
        "Surface_AllWeather": 0.0, "Surface_Dirt": 0.0, "Surface_Turf": 1.0,
        "Going_Good": 1.0, "Going_Good_To_Soft": 0.0, "Going_Soft": 0.0,
        "Going_Good_To_Firm": 0.0, "Going_Firm": 0.0, "Going_Heavy": 0.0,
        "RaceType_Flat": 1.0, "RaceType_Hurdle": 0.0,
        "RaceType_Other": 0.0, "RaceType_SteepleChase": 0.0,
    }


# ================================================================
# _compute_horse_stats
# ================================================================

def test_horse_stats_one_row_per_horse():
    rows = [
        _train_row(horse_id=1, jockey_id=10, off="2026-01-01"),
        _train_row(horse_id=1, jockey_id=10, off="2026-02-01"),
        _train_row(horse_id=2, jockey_id=20, off="2026-01-15"),
    ]
    result = _compute_horse_stats(pd.DataFrame(rows))
    assert len(result) == 2
    assert set(result["HorseId"]) == {1, 2}


def test_horse_stats_uses_most_recent_race_as_last_off():
    rows = [
        _train_row(horse_id=1, jockey_id=10, off="2026-01-01", speed=14.0),
        _train_row(horse_id=1, jockey_id=10, off="2026-03-01", speed=16.0),
    ]
    result = _compute_horse_stats(pd.DataFrame(rows))
    row = result[result["HorseId"] == 1].iloc[0]
    assert row["LastOff"] == pd.Timestamp("2026-03-01")
    assert row["LastRaceSpeed"] == pytest.approx(16.0)


def test_horse_stats_has_required_columns():
    rows = [_train_row(horse_id=1, jockey_id=10, off="2026-01-01")]
    result = _compute_horse_stats(pd.DataFrame(rows))
    for col in [
        "HorseId", "LastOff", "LastRaceDistanceInMeters",
        "LastRaceWeightInPounds", "LastRaceSpeed",
        "LastRaceAvgRelFinishingPosition",
        "LastRaceSurface_Turf", "LastRaceGoing_Good", "LastRaceRaceType_Flat",
    ]:
        assert col in result.columns, f"Missing column: {col}"


def test_horse_stats_avg_rel_pos_incorporates_last_race():
    # n_prior=4, last_avg_rel_pos=0.4, finishing_pos=1, horse_count=5
    # updated = (0.4*4 + 1/5) / 5 = (1.6+0.2)/5 = 0.36
    rows = [_train_row(
        horse_id=1, jockey_id=10, off="2026-01-01",
        finishing_pos=1, horse_count=5,
        n_prior=4.0, last_avg_rel_pos=0.4,
    )]
    result = _compute_horse_stats(pd.DataFrame(rows))
    assert result.iloc[0]["LastRaceAvgRelFinishingPosition"] == pytest.approx(0.36)


# ================================================================
# _compute_jockey_stats
# ================================================================

def test_jockey_stats_one_row_per_jockey():
    rows = [
        _train_row(horse_id=1, jockey_id=10, off="2026-01-01"),
        _train_row(horse_id=2, jockey_id=10, off="2026-02-01"),
        _train_row(horse_id=3, jockey_id=20, off="2026-01-15"),
    ]
    result = _compute_jockey_stats(pd.DataFrame(rows))
    assert len(result) == 2
    assert set(result["JockeyId"]) == {10, 20}


def test_jockey_stats_has_required_columns():
    rows = [_train_row(horse_id=1, jockey_id=10, off="2026-01-01")]
    result = _compute_jockey_stats(pd.DataFrame(rows))
    for col in [
        "JockeyId", "LastOff", "JockeyNumberOfPriorRaces",
        "JockeyWinPercentage", "JockeyTop3Percentage",
        "JockeyAvgRelFinishingPosition",
    ]:
        assert col in result.columns, f"Missing column: {col}"


def test_jockey_stats_excludes_jockey_id_zero():
    rows = [
        _train_row(horse_id=1, jockey_id=0, off="2026-01-01"),
        _train_row(horse_id=2, jockey_id=10, off="2026-01-01"),
    ]
    result = _compute_jockey_stats(pd.DataFrame(rows))
    assert 0 not in result["JockeyId"].values
    assert len(result) == 1


def test_jockey_stats_uses_most_recent_race_as_last_off():
    rows = [
        _train_row(horse_id=1, jockey_id=10, off="2026-01-01"),
        _train_row(horse_id=2, jockey_id=10, off="2026-03-01"),
    ]
    result = _compute_jockey_stats(pd.DataFrame(rows))
    assert result[result["JockeyId"] == 10].iloc[0]["LastOff"] == pd.Timestamp("2026-03-01")


# ================================================================
# _format_timing
# ================================================================

def test_format_timing_returns_pipe_prefixed_string():
    from race_analytics.scripts.evaluate import _format_timing
    assert _format_timing(1.234, 0.056) == "| fit=1.234s, predict=0.056s"


def test_format_timing_three_decimal_places():
    from race_analytics.scripts.evaluate import _format_timing
    result = _format_timing(0.1, 0.001)
    assert "fit=0.100s" in result
    assert "predict=0.001s" in result


# ================================================================
# _aggregate_times
# ================================================================

def test_aggregate_times_returns_mean_and_std():
    from race_analytics.scripts.evaluate import _aggregate_times
    mean, std = _aggregate_times([1.0, 2.0, 3.0])
    assert mean == pytest.approx(2.0)
    assert std == pytest.approx(np.std([1.0, 2.0, 3.0]))


def test_aggregate_times_single_value_has_zero_std():
    from race_analytics.scripts.evaluate import _aggregate_times
    mean, std = _aggregate_times([5.0])
    assert mean == pytest.approx(5.0)
    assert std == pytest.approx(0.0)


def test_aggregate_times_empty_returns_none():
    from race_analytics.scripts.evaluate import _aggregate_times
    assert _aggregate_times([]) is None


# ================================================================
# evaluate() — timing accumulation
# ================================================================

def _make_fold_races(fold_date):
    """Minimal two-row DataFrame: one training row + one known fold row."""
    train_date = fold_date - timedelta(days=1)
    return pd.DataFrame([
        {
            "Off": pd.Timestamp(train_date), "KnownHorseAndJockey": False,
            "RaceId": 1, "HorseId": 10, "JockeyId": 100, "TrainerId": 1000,
            "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
            "DistanceInMeters": 1600.0, "WeightInPounds": 126.0,
            "FinishingPosition": 2, "DecimalOdds": 3.5, "ResultStatus": "CompletedRace",
            "HorseName": "TrainHorse", "CourseName": "Cheltenham",
        },
        {
            "Off": pd.Timestamp(fold_date), "KnownHorseAndJockey": True,
            "RaceId": 2, "HorseId": 20, "JockeyId": 200, "TrainerId": 2000,
            "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
            "DistanceInMeters": 1600.0, "WeightInPounds": 126.0,
            "FinishingPosition": 1, "DecimalOdds": 3.5, "ResultStatus": "CompletedRace",
            "HorseName": "FoldHorse", "CourseName": "Ascot",
        },
    ])


class _StubAlgo:
    def fit(self, _train_df):
        pass

    def predict(self, card, *_args):
        if card.empty:
            return pd.DataFrame(columns=["RaceId", "HorseId"])
        return pd.DataFrame([{"RaceId": int(card["RaceId"].iloc[0]), "HorseId": int(card["HorseId"].iloc[0])}])


def test_evaluate_timing_summary_printed_after_accuracy_summary(capsys):
    from race_analytics.scripts.evaluate import evaluate

    fold_date = date.today() - timedelta(days=1)
    stub_algo = _StubAlgo()

    with (
        patch("race_analytics.scripts.evaluate._load_window", return_value=pd.DataFrame([{"x": 1}])),
        patch("race_analytics.scripts.evaluate._engineer_features", return_value=_make_fold_races(fold_date)),
        patch("race_analytics.scripts.evaluate.extract_horse_stats", return_value=pd.DataFrame()),
        patch("race_analytics.scripts.evaluate.extract_jockey_stats", return_value=pd.DataFrame()),
        patch("race_analytics.scripts.evaluate.extract_trainer_stats", return_value=pd.DataFrame()),
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


def test_evaluate_timing_summary_shows_na_for_skipped_algorithms(capsys):
    from race_analytics.scripts.evaluate import evaluate

    # Return empty raw data so all folds are skipped (no known races)
    with (
        patch("race_analytics.scripts.evaluate._load_window", return_value=pd.DataFrame()),
        patch("race_analytics.scripts.evaluate.ALGORITHMS", [_StubAlgo()]),
    ):
        evaluate(folds=1)

    out = capsys.readouterr().out
    assert "=== Timing Summary ===" in out
    assert "N/A" in out


def test_evaluate_timing_accumulators_have_one_entry_per_completed_fold():
    from race_analytics.scripts.evaluate import evaluate

    fold_date = date.today() - timedelta(days=1)
    stub_algo = _StubAlgo()

    with (
        patch("race_analytics.scripts.evaluate._load_window", return_value=pd.DataFrame([{"x": 1}])),
        patch("race_analytics.scripts.evaluate._engineer_features", return_value=_make_fold_races(fold_date)),
        patch("race_analytics.scripts.evaluate.extract_horse_stats", return_value=pd.DataFrame()),
        patch("race_analytics.scripts.evaluate.extract_jockey_stats", return_value=pd.DataFrame()),
        patch("race_analytics.scripts.evaluate.extract_trainer_stats", return_value=pd.DataFrame()),
        patch("race_analytics.scripts.evaluate.ALGORITHMS", [stub_algo]),
    ):
        timing = evaluate(folds=1)

    name = "_StubAlgo"
    assert name in timing["fit_times"], f"Expected '{name}' key; got {list(timing['fit_times'])}"
    assert len(timing["fit_times"][name]) == 1
    assert len(timing["predict_times"][name]) == 1
    assert timing["fit_times"][name][0] >= 0.0
    assert timing["predict_times"][name][0] >= 0.0
