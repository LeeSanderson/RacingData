"""Tests for the canonical RaceData value object + RaceDataBuilder (issue 002).

The headline gate is `test_from_legacy_reproduces_run_prediction_intermediate`: it
builds the post-encode `merged` frame with an independent, frozen reimplementation of
the legacy `_run_prediction` merge + transform sequence and asserts that
`RaceDataBuilder.from_legacy(...)` reproduces it column-for-column. (The production
`_run_prediction` body was folded into the engine in issue 004; this reference is the
behavioural snapshot it used to be characterised against.) `as_of` is fixed so
`DaysRested` is deterministic.
"""

from datetime import datetime

import numpy as np
import pandas as pd

from race_analytics.algorithms.base import REQUIRED_PREDICTORS, OPTIONAL_PREDICTORS
from race_analytics.features.race_data import RaceData, RaceDataBuilder
from race_analytics.features.race_history import race_card
from race_analytics.features.horse_stats import extract_horse_stats
from race_analytics.features.jockey_stats import extract_jockey_stats
from race_analytics.features.trainer_stats import extract_trainer_stats
from race_analytics.features.transforms import (
    encode_surfaces,
    encode_going,
    encode_race_type,
    calculate_weight_change,
    calculate_distance_change,
    calculate_surface_switch,
    calculate_code_switch,
    calculate_race_class,
    calculate_age_features,
    calculate_draw_features,
    encode_pattern,
    calculate_is_handicap,
    encode_age_band,
    encode_sex_restriction,
    encode_headgear,
)

_AS_OF = datetime(2026, 6, 13, 9, 30, 0)


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


def _legacy_reference_merged(races, horse_stats, jockey_stats, trainer_stats):
    """Frozen reimplementation of the legacy `_run_prediction` merge + transform
    sequence, independent of production code. `as_of` is pinned to `_AS_OF` so
    `DaysRested` is deterministic."""
    today = np.datetime64(_AS_OF)
    one_day = np.timedelta64(1, "D")

    merged = pd.merge(races.copy(), horse_stats, how="left", on=["HorseId"])
    merged["DaysRested"] = np.ceil((today - pd.to_datetime(merged["LastOff"])) / one_day)
    merged.loc[merged["DaysRested"] > 10, "DaysRested"] = 10
    merged = merged.drop("LastOff", axis=1, errors="ignore")

    merged = pd.merge(merged, jockey_stats, how="left", on=["JockeyId"])
    merged["DaysSinceJockeyLastRaced"] = np.ceil(
        (today - pd.to_datetime(merged["LastOff"])) / one_day
    )
    merged.loc[merged["DaysSinceJockeyLastRaced"] > 10, "DaysSinceJockeyLastRaced"] = 10
    merged = merged.drop("LastOff", axis=1, errors="ignore")

    if trainer_stats is not None:
        merged = pd.merge(merged, trainer_stats, how="left", on=["TrainerId"])

    merged = encode_surfaces(merged)
    merged = encode_going(merged)
    merged = encode_race_type(merged)
    merged = calculate_weight_change(merged)
    merged = calculate_distance_change(merged)
    merged = calculate_surface_switch(merged)
    merged = calculate_code_switch(merged)
    merged = calculate_race_class(merged)
    merged = calculate_age_features(merged)
    merged = encode_pattern(merged)
    merged = calculate_is_handicap(merged)
    merged = encode_age_band(merged)
    merged = encode_sex_restriction(merged)
    merged = encode_headgear(merged)
    if "HorseCount" not in merged.columns:
        merged["HorseCount"] = merged.groupby("RaceId")["HorseId"].transform("count")
    merged = calculate_draw_features(merged)
    return merged


# ── characterization (the must-pass gate) ──────────────────────────────────────


def test_from_legacy_reproduces_run_prediction_intermediate():
    races, hs, js, ts = _races(), _horse_stats(), _jockey_stats(), _trainer_stats()
    legacy = _legacy_reference_merged(races, hs, js, ts)
    rd = RaceDataBuilder().from_legacy(races, hs, js, ts, as_of=_AS_OF)
    pd.testing.assert_frame_equal(rd.frame, legacy)


def test_from_legacy_without_trainer_stats():
    races, hs, js = _races(), _horse_stats(), _jockey_stats()
    legacy = _legacy_reference_merged(races, hs, js, None)
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


# ── wrap_training: wrap an already-enriched frame WITHOUT re-running the chain ──


def test_wrap_training_does_not_re_run_canonical_chain():
    """The harness feeds wrap_training a frame already enriched by _engineer_features
    (which does NOT compute WeightChange/DistanceChange/SurfaceSwitch/CodeSwitch).
    Unlike build_training, wrap_training must NOT add those columns — re-encoding
    would change the selected feature set and the fitted model."""
    hist = _enriched_history()
    for col in ("WeightChange", "DistanceChange", "SurfaceSwitch", "CodeSwitch"):
        assert col not in hist.columns
    rd = RaceDataBuilder().wrap_training(hist, max_horses=10)
    for col in ("WeightChange", "DistanceChange", "SurfaceSwitch", "CodeSwitch"):
        assert col not in rd.frame.columns, f"{col} was added — chain was re-run"


def test_wrap_training_clamps_day_since_features():
    hist = _enriched_history()
    hist["DaysRested"] = 99.0
    hist["DaysSinceJockeyLastRaced"] = 50.0
    rd = RaceDataBuilder().wrap_training(hist, max_horses=10)
    assert (rd.frame["DaysRested"] == 10).all()
    assert (rd.frame["DaysSinceJockeyLastRaced"] == 10).all()


def test_wrap_training_as_of_is_one_day_past_last_race():
    hist = _enriched_history()
    hist.loc[hist.index[-1], "Off"] = pd.Timestamp("2026-05-10 14:00:00")
    rd = RaceDataBuilder().wrap_training(hist, max_horses=10)
    assert rd.as_of == pd.Timestamp("2026-05-11")


def test_wrap_training_retains_labels():
    rd = RaceDataBuilder().wrap_training(_enriched_history(), max_horses=10)
    assert rd.has_labels is True


def test_wrap_training_matches_legacy_training_adapter():
    """wrap_training reproduces the base algorithm's _training_data_from_legacy
    exactly (the path the un-migrated harness uses today via algo.fit(flat_frame))."""
    from race_analytics.algorithms.win_classifier import WinClassifier

    hist = _enriched_history()
    hist["DaysRested"] = 99.0
    legacy = WinClassifier(max_horses=10)._training_data_from_legacy(hist)
    wrapped = RaceDataBuilder().wrap_training(hist, max_horses=10)
    pd.testing.assert_frame_equal(wrapped.frame, legacy.frame)
    assert wrapped.as_of == legacy.as_of
    assert wrapped.max_horses == legacy.max_horses


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
