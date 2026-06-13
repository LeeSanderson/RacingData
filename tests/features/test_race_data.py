"""Tests for the canonical RaceData value object + RaceDataBuilder (issue 002).

The headline gate is `test_from_legacy_reproduces_run_prediction_intermediate`: it
captures the *actual* post-encode `merged` frame that the live
`BinaryWinClassifierAlgorithm._run_prediction` builds and asserts that
`RaceDataBuilder.from_legacy(...)` reproduces it column-for-column. `datetime.today()`
is pinned so `DaysRested` is deterministic.
"""

from datetime import datetime
from unittest import mock

import numpy as np
import pandas as pd

from race_analytics.algorithms import binary_win_classifier as bwc_module
from race_analytics.algorithms.binary_win_classifier import BinaryWinClassifierAlgorithm
from race_analytics.algorithms.base import REQUIRED_PREDICTORS, OPTIONAL_PREDICTORS
from race_analytics.features.race_data import RaceData, RaceDataBuilder
from race_analytics.features.race_history import race_card
from race_analytics.features.horse_stats import extract_horse_stats
from race_analytics.features.jockey_stats import extract_jockey_stats
from race_analytics.features.trainer_stats import extract_trainer_stats

_AS_OF = datetime(2026, 6, 13, 9, 30, 0)


class _MockClassifier:
    def fit(self, X, y, **kwargs):
        return self

    def predict_proba(self, X):
        out = np.zeros((len(X), 2))
        out[:, 1] = 0.5
        return out


# ── fixtures (raw card + per-entity stats, as predict() would receive) ─────────


def _races() -> pd.DataFrame:
    rows = []
    for r in (1, 2):
        for h in range(3):
            hid = r * 10 + h
            rows.append({
                "RaceId": r, "HorseId": hid, "JockeyId": hid, "TrainerId": hid,
                "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
                "DistanceInMeters": 1600.0, "WeightInPounds": 130.0,
                "Class": "3", "Age": 4, "StallNumber": h + 1,
                "Pattern": "", "RatingBand": "0-100", "AgeBand": "3yo+",
                "SexRestriction": "", "HeadGear": "b" if h == 0 else "",
            })
    return pd.DataFrame(rows)


def _horse_stats() -> pd.DataFrame:
    rows = []
    for r in (1, 2):
        for h in range(3):
            hid = r * 10 + h
            rows.append({
                "HorseId": hid,
                "LastOff": pd.Timestamp(f"2026-05-{10 + h:02d}"),
                "NumberOfPriorRaces": 5.0,
                "LastRaceDistanceInMeters": 1500.0,
                "LastRaceWeightInPounds": 128.0,
                "LastRaceSpeed": 15.0,
                "LastRaceAvgRelFinishingPosition": 0.4,
                "LastRaceSurface_Turf": 1.0, "LastRaceSurface_Dirt": 0.0,
                "LastRaceSurface_AllWeather": 0.0,
                "LastRaceRaceType_Flat": 1.0, "LastRaceRaceType_Hurdle": 0.0,
                "LastRaceRaceType_SteepleChase": 0.0, "LastRaceRaceType_Other": 0.0,
            })
    return pd.DataFrame(rows)


def _jockey_stats() -> pd.DataFrame:
    rows = []
    for r in (1, 2):
        for h in range(3):
            jid = r * 10 + h
            rows.append({
                "JockeyId": jid,
                "LastOff": pd.Timestamp(f"2026-05-{12 + h:02d}"),
                "JockeyNumberOfPriorRaces": 50.0,
                "JockeyWinPercentage": 0.15,
                "JockeyTop3Percentage": 0.4,
                "JockeyAvgRelFinishingPosition": 0.45,
            })
    return pd.DataFrame(rows)


def _trainer_stats() -> pd.DataFrame:
    rows = []
    for r in (1, 2):
        for h in range(3):
            tid = r * 10 + h
            rows.append({
                "TrainerId": tid,
                "TrainerNumberOfPriorRaces": 80.0,
                "TrainerWinPercentage": 0.12,
                "TrainerTop3Percentage": 0.35,
                "TrainerAvgRelFinishingPosition": 0.48,
            })
    return pd.DataFrame(rows)


def _enriched_history() -> pd.DataFrame:
    """A flat, fully-engineered race_history frame (one row per horse) — what a
    training window looks like, sufficient for the extract_*_stats functions."""
    df = _races().copy()
    df["Off"] = pd.Timestamp("2026-05-01")
    df["FinishingPosition"] = [1, 2, 3, 1, 2, 3]
    df["HorseCount"] = 3
    df["Speed"] = 15.0
    df["Wins"] = (df["FinishingPosition"] == 1).astype(int)
    df["NumberOfPriorRaces"] = 5.0
    df["LastRaceAvgRelFinishingPosition"] = 0.4
    df["OfficialRating"] = 80.0
    df["RacingPostRating"] = 90.0
    df["TopSpeedRating"] = 85.0
    df["DaysRested"] = 30.0
    df["DaysSinceJockeyLastRaced"] = 12.0
    df["JockeyNumberOfPriorRaces"] = 50.0
    df["JockeyWinPercentage"] = 0.15
    df["JockeyTop3Percentage"] = 0.4
    df["JockeyAvgRelFinishingPosition"] = 0.45
    df["TrainerNumberOfPriorRaces"] = 80.0
    df["TrainerWinPercentage"] = 0.12
    df["TrainerTop3Percentage"] = 0.35
    df["TrainerAvgRelFinishingPosition"] = 0.48
    # current-race one-hots (extract_horse_stats reads these to build LastRace*)
    for col in ("Surface_Turf", "Surface_Dirt", "Surface_AllWeather"):
        df[col] = 1.0 if col == "Surface_Turf" else 0.0
    for col in ("Going_Good", "Going_Good_To_Soft", "Going_Soft",
                "Going_Good_To_Firm", "Going_Firm", "Going_Heavy"):
        df[col] = 1.0 if col == "Going_Good" else 0.0
    for col in ("RaceType_Flat", "RaceType_Hurdle",
                "RaceType_SteepleChase", "RaceType_Other"):
        df[col] = 1.0 if col == "RaceType_Flat" else 0.0
    # stored LastRace* (a real enriched frame already has these)
    df["LastRaceDistanceInMeters"] = 1500.0
    df["LastRaceWeightInPounds"] = 128.0
    df["LastRaceSpeed"] = 15.0
    for col in ("LastRaceSurface_Turf", "LastRaceSurface_Dirt", "LastRaceSurface_AllWeather"):
        df[col] = 1.0 if col == "LastRaceSurface_Turf" else 0.0
    for col in ("LastRaceGoing_Good", "LastRaceGoing_Good_To_Soft", "LastRaceGoing_Soft",
                "LastRaceGoing_Good_To_Firm", "LastRaceGoing_Firm", "LastRaceGoing_Heavy"):
        df[col] = 1.0 if col == "LastRaceGoing_Good" else 0.0
    for col in ("LastRaceRaceType_Flat", "LastRaceRaceType_Hurdle",
                "LastRaceRaceType_SteepleChase", "LastRaceRaceType_Other"):
        df[col] = 1.0 if col == "LastRaceRaceType_Flat" else 0.0
    df["Last3RaceAvgSpeed"] = np.nan
    df["Last3RaceSpeedTrend"] = np.nan
    df["Last3AvgRelFinishingPosition"] = np.nan
    return df


def _capture_legacy_merged(races, horse_stats, jockey_stats, trainer_stats):
    """Run the live _run_prediction and capture its post-encode `merged` frame."""
    algo = BinaryWinClassifierAlgorithm(_MockClassifier())
    algo._feature_cols = ["DistanceInMeters"]  # non-empty so _run_prediction proceeds
    captured = {}
    real_draw = bwc_module.calculate_draw_features

    def _capture(df):
        out = real_draw(df)
        captured["merged"] = out.copy()
        return out

    with mock.patch.object(bwc_module, "calculate_draw_features", _capture), \
            mock.patch.object(bwc_module, "datetime") as m_dt:
        m_dt.today.return_value = _AS_OF
        algo.predict_field(races, horse_stats, jockey_stats, trainer_stats)
    return captured["merged"]


# ── characterization (the must-pass gate) ──────────────────────────────────────


def test_from_legacy_reproduces_run_prediction_intermediate():
    races, hs, js, ts = _races(), _horse_stats(), _jockey_stats(), _trainer_stats()
    legacy = _capture_legacy_merged(races, hs, js, ts)
    rd = RaceDataBuilder().from_legacy(races, hs, js, ts, as_of=_AS_OF)
    pd.testing.assert_frame_equal(rd.frame, legacy)


def test_from_legacy_without_trainer_stats():
    races, hs, js = _races(), _horse_stats(), _jockey_stats()
    legacy = _capture_legacy_merged(races, hs, js, None)
    rd = RaceDataBuilder().from_legacy(races, hs, js, None, as_of=_AS_OF)
    pd.testing.assert_frame_equal(rd.frame, legacy)


def test_from_legacy_does_not_mutate_inputs():
    races = _races()
    before = races.copy()
    RaceDataBuilder().from_legacy(races, _horse_stats(), _jockey_stats(), _trainer_stats(), as_of=_AS_OF)
    pd.testing.assert_frame_equal(races, before)


def test_from_legacy_clamps_days_rested_to_ten():
    # LastOff far in the past -> raw DaysRested >> 10, must clamp to 10.
    races = _races()
    hs = _horse_stats()
    hs["LastOff"] = pd.Timestamp("2020-01-01")
    rd = RaceDataBuilder().from_legacy(races, hs, _jockey_stats(), _trainer_stats(), as_of=_AS_OF)
    assert (rd.frame["DaysRested"] == 10).all()


# ── builder parity: training vs serving ────────────────────────────────────────


def test_build_serving_matches_from_legacy_over_decomposed_history():
    hist = _enriched_history()
    card = race_card(hist)
    as_of = pd.Timestamp("2026-06-13")
    builder = RaceDataBuilder()
    serve = builder.build_serving(card, hist, as_of)
    legacy = builder.from_legacy(
        card, extract_horse_stats(hist), extract_jockey_stats(hist),
        extract_trainer_stats(hist), as_of,
    )
    pd.testing.assert_frame_equal(serve.frame, legacy.frame)


def test_build_training_and_serving_expose_same_feature_columns():
    hist = _enriched_history()
    card = race_card(hist)
    as_of = pd.Timestamp("2026-06-13")
    builder = RaceDataBuilder()
    train = builder.build_training(hist, as_of)
    serve = builder.build_serving(card, hist, as_of)
    universe = REQUIRED_PREDICTORS + OPTIONAL_PREDICTORS
    train_feats = [c for c in universe if c in train.frame.columns]
    serve_feats = [c for c in universe if c in serve.frame.columns]
    assert train_feats == serve_feats
    assert train_feats  # non-empty


def test_build_training_has_labels_serving_does_not():
    hist = _enriched_history()
    as_of = pd.Timestamp("2026-06-13")
    builder = RaceDataBuilder()
    assert builder.build_training(hist, as_of).has_labels is True
    assert builder.build_serving(race_card(hist), hist, as_of).has_labels is False


def test_build_training_clamps_days_rested():
    hist = _enriched_history()
    hist["DaysRested"] = 99.0
    rd = RaceDataBuilder().build_training(hist, pd.Timestamp("2026-06-13"))
    assert (rd.frame["DaysRested"] == 10).all()


# ── RaceData value-object semantics ────────────────────────────────────────────


def test_has_labels_detects_label_columns():
    as_of = pd.Timestamp("2026-06-13")
    assert RaceData(pd.DataFrame({"RaceId": [1], "Wins": [1]}), as_of).has_labels is True
    assert RaceData(pd.DataFrame({"RaceId": [1], "Speed": [15.0]}), as_of).has_labels is True
    assert RaceData(pd.DataFrame({"RaceId": [1], "HorseId": [2]}), as_of).has_labels is False


def test_feature_frame_selects_requested_columns_in_order():
    df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
    rd = RaceData(df, pd.Timestamp("2026-06-13"))
    assert list(rd.feature_frame(["c", "a"]).columns) == ["c", "a"]


def test_with_columns_is_copy_on_write():
    df = pd.DataFrame({"RaceId": [1, 2]})
    rd = RaceData(df, pd.Timestamp("2026-06-13"), max_horses=8)
    rd2 = rd.with_columns(x=[10, 20])
    assert "x" not in rd.frame.columns      # original untouched
    assert list(rd2.frame["x"]) == [10, 20]
    assert rd2.as_of == rd.as_of and rd2.max_horses == 8


def test_subset_filters_rows_copy_on_write():
    df = pd.DataFrame({"RaceId": [1, 2, 3]})
    rd = RaceData(df, pd.Timestamp("2026-06-13"))
    rd2 = rd.subset(df["RaceId"] > 1)
    assert list(rd2.frame["RaceId"]) == [2, 3]
    assert len(rd.frame) == 3               # original untouched
