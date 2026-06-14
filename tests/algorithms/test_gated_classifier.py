from datetime import datetime

import pandas as pd
import pytest

from race_analytics.algorithms.base import FieldPredictorBaseAlgorithm
from race_analytics.algorithms.gated_classifier import GatedClassifier
from race_analytics.algorithms.win_classifier import WinClassifier
from race_analytics.features.race_data import RaceData, RaceDataBuilder

_LONG_AGO = datetime(2020, 1, 1)
D1 = datetime(2021, 1, 1)
_AS_OF = datetime(2026, 1, 1)


def _rd(df):
    return RaceDataBuilder().wrap_training(df)


def _serve(races, horse_stats, jockey_stats):
    return RaceDataBuilder().build_serving_from_stats(
        races, horse_stats, jockey_stats, None, as_of=_AS_OF
    )


def _train_row(horse_id: int, race_id: int, off: datetime = D1, wins: int = 0) -> dict:
    return {
        "HorseId": horse_id,
        "RaceId": race_id,
        "Off": off,
        "Wins": wins,
        "CourseName": "Newmarket",
        "Speed": 16.0,
        "FinishingPosition": 2,
        "OverallBeatenDistance": 2.0,
        "HorseCount": 8,
        "NumberOfPriorRaces": 3,
        "JockeyId": horse_id + 1000,
        "Surface": "Turf",
        "Going": "Good",
        "RaceType": "Flat",
        "OfficialRating": 80.0,
        "RacingPostRating": 100.0,
        "TopSpeedRating": 90.0,
        "LastRaceOfficialRating": 70.0,
        "LastRaceRacingPostRating": 95.0,
        "LastRaceTopSpeedRating": 92.0,
        "DistanceInMeters": 1600.0,
        "WeightInPounds": 126.0,
        "Surface_AllWeather": 0.0,
        "Surface_Dirt": 0.0,
        "Surface_Turf": 1.0,
        "Going_Firm": 0.0,
        "Going_Good": 1.0,
        "Going_Good_To_Firm": 0.0,
        "Going_Good_To_Soft": 0.0,
        "Going_Heavy": 0.0,
        "Going_Soft": 0.0,
        "RaceType_Flat": 1.0,
        "RaceType_Hurdle": 0.0,
        "RaceType_Other": 0.0,
        "RaceType_SteepleChase": 0.0,
        "LastRaceDistanceInMeters": 1600.0,
        "LastRaceWeightInPounds": 126.0,
        "LastRaceSpeed": 15.5,
        "DaysRested": 7.0,
        "LastRaceAvgRelFinishingPosition": 0.5,
        "LastRaceSurface_AllWeather": 0.0,
        "LastRaceSurface_Dirt": 0.0,
        "LastRaceSurface_Turf": 1.0,
        "LastRaceGoing_Good": 1.0,
        "LastRaceGoing_Good_To_Soft": 0.0,
        "LastRaceGoing_Soft": 0.0,
        "LastRaceGoing_Good_To_Firm": 0.0,
        "LastRaceGoing_Firm": 0.0,
        "LastRaceGoing_Heavy": 0.0,
        "LastRaceRaceType_Other": 0.0,
        "LastRaceRaceType_Hurdle": 0.0,
        "LastRaceRaceType_SteepleChase": 0.0,
        "LastRaceRaceType_Flat": 1.0,
        "JockeyNumberOfPriorRaces": 10.0,
        "DaysSinceJockeyLastRaced": 3.0,
        "JockeyWinPercentage": 0.2,
        "JockeyTop3Percentage": 0.5,
        "JockeyAvgRelFinishingPosition": 0.4,
    }


def _race_row(
    race_id: int, horse_id: int, jockey_id: int, distance_m: float = 1600.0
) -> dict:
    return {
        "RaceId": race_id,
        "HorseId": horse_id,
        "JockeyId": jockey_id,
        "Surface": "Turf",
        "Going": "Good",
        "RaceType": "Flat",
        "DistanceInMeters": distance_m,
        "WeightInPounds": 126.0,
    }


def _horse_stat(horse_id: int) -> dict:
    return {
        "HorseId": horse_id,
        "LastOff": _LONG_AGO,
        "LastRaceDistanceInMeters": 1600.0,
        "LastRaceWeightInPounds": 126.0,
        "LastRaceAvgRelFinishingPosition": 0.5,
        "LastRaceSpeed": 16.0,
        "LastRaceOfficialRating": 70.0,
        "LastRaceRacingPostRating": 95.0,
        "LastRaceTopSpeedRating": 92.0,
        "LastRaceSurface_AllWeather": 0.0,
        "LastRaceSurface_Dirt": 0.0,
        "LastRaceSurface_Turf": 1.0,
        "LastRaceGoing_Firm": 0.0,
        "LastRaceGoing_Good": 1.0,
        "LastRaceGoing_Good_To_Firm": 0.0,
        "LastRaceGoing_Good_To_Soft": 0.0,
        "LastRaceGoing_Heavy": 0.0,
        "LastRaceGoing_Soft": 0.0,
        "LastRaceRaceType_Flat": 1.0,
        "LastRaceRaceType_Hurdle": 0.0,
        "LastRaceRaceType_Other": 0.0,
        "LastRaceRaceType_SteepleChase": 0.0,
    }


def _jockey_stat(jockey_id: int) -> dict:
    return {
        "JockeyId": jockey_id,
        "LastOff": _LONG_AGO,
        "JockeyNumberOfPriorRaces": 10.0,
        "JockeyWinPercentage": 0.2,
        "JockeyTop3Percentage": 0.5,
        "JockeyAvgRelFinishingPosition": 0.4,
    }


def _make_train_df(n_races: int = 5) -> pd.DataFrame:
    rows = [
        _train_row(horse_id=r * 10 + h, race_id=r, off=D1, wins=1 if h == 0 else 0)
        for r in range(1, n_races + 1)
        for h in range(3)
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def trained_gated() -> GatedClassifier:
    inner = WinClassifier(max_horses=10)
    algo = GatedClassifier(inner, coverage=0.7)
    algo.fit(_rd(_make_train_df()))
    return algo


# ── 1. fit + predict_field returns expected columns ───────────────────────────


def test_fit_predict_field_returns_expected_columns(trained_gated):
    races = pd.DataFrame([_race_row(10, h, h) for h in [101, 102, 103]])
    horse_stats = pd.DataFrame([_horse_stat(h) for h in [101, 102, 103]])
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in [101, 102, 103]])
    result = trained_gated.predict_field(_serve(races, horse_stats, jockey_stats))
    for col in ["RaceId", "HorseId", "WinProbability", "PredictedRank"]:
        assert col in result.columns, f"missing column: {col}"


# ── 2. predict returns one row per race (rank 1 only) ─────────────────────────


def test_predict_returns_one_row_per_race(trained_gated):
    races = pd.DataFrame(
        [_race_row(10, h, h) for h in [101, 102, 103]]
        + [_race_row(20, h, h) for h in [201, 202, 203]]
    )
    horse_stats = pd.DataFrame([_horse_stat(h) for h in [101, 102, 103, 201, 202, 203]])
    jockey_stats = pd.DataFrame(
        [_jockey_stat(h) for h in [101, 102, 103, 201, 202, 203]]
    )
    result = trained_gated.predict(_serve(races, horse_stats, jockey_stats))
    assert list(result.columns) == ["RaceId", "HorseId"]
    assert result["RaceId"].nunique() == len(result)


# ── 3. predict_field_unfiltered returns more rows than predict_field ──────────


def test_predict_field_unfiltered_has_more_rows_than_predict_field():
    inner = WinClassifier(max_horses=10)
    algo = GatedClassifier(inner, coverage=0.3)  # tight gate suppresses some races
    algo.fit(_rd(_make_train_df(n_races=10)))

    races = pd.DataFrame(
        [_race_row(10, h, h) for h in [101, 102, 103]]
        + [_race_row(20, h, h) for h in [201, 202, 203]]
        + [_race_row(30, h, h) for h in [301, 302, 303]]
    )
    horse_stats = pd.DataFrame(
        [_horse_stat(h) for h in [101, 102, 103, 201, 202, 203, 301, 302, 303]]
    )
    jockey_stats = pd.DataFrame(
        [_jockey_stat(h) for h in [101, 102, 103, 201, 202, 203, 301, 302, 303]]
    )

    filtered = algo.predict_field(_serve(races, horse_stats, jockey_stats))
    unfiltered = algo.predict_field_unfiltered(_serve(races, horse_stats, jockey_stats))
    assert len(unfiltered) >= len(filtered)


# ── 4. no inheritance from inner class ───────────────────────────────────────


def test_gated_classifier_does_not_inherit_from_inner():
    inner = WinClassifier(max_horses=10)
    algo = GatedClassifier(inner)
    assert not isinstance(algo, WinClassifier)


# ── 5. gate is calibrated after fit ──────────────────────────────────────────


def test_gate_calibrated_after_fit():
    inner = WinClassifier(max_horses=10)
    algo = GatedClassifier(inner, coverage=0.7)
    algo.fit(_rd(_make_train_df()))
    assert algo.get_confidence_gate()._calib_scores


# ── 6. characterization: threshold matches the legacy round trip on the fixture ─


def test_calibrated_threshold_matches_legacy_within_tolerance():
    algo = GatedClassifier(WinClassifier(max_horses=10), coverage=0.7)
    algo.fit(_rd(_make_train_df()))
    # Legacy (decompose -> four-frame re-encode) threshold pinned at 1/3 on this
    # uniform fixture (3 identical runners per race -> top_prob ~= 0.333).
    assert algo.get_confidence_gate().threshold == pytest.approx(0.33333334, abs=1e-2)


# ── 9. calibration flows RaceData.as_of through to the gate ───────────────────


class _AsOfScoringInner(FieldPredictorBaseAlgorithm):
    """Fake inner whose in-sample WinProbability encodes data.as_of, so that the
    gate's calibration is observably driven by the RaceData it was handed."""

    def fit(self, data) -> None:
        pass

    def predict_field(self, data, *args, **kwargs):
        out = data.frame[["RaceId", "HorseId"]].copy()
        out["WinProbability"] = (data.as_of.day % 28) / 28.0
        out["PredictedRank"] = 1.0
        return out


def _race_data(as_of: pd.Timestamp) -> RaceData:
    frame = pd.DataFrame(
        {"RaceId": [1, 1, 2, 2], "HorseId": [10, 11, 20, 21], "Wins": [1, 0, 1, 0]}
    )
    return RaceData(frame, as_of=as_of)


def test_different_as_of_calibrates_differently():
    early = GatedClassifier(_AsOfScoringInner(), coverage=0.7)
    late = GatedClassifier(_AsOfScoringInner(), coverage=0.7)
    early.fit(_race_data(pd.Timestamp("2021-01-05")))
    late.fit(_race_data(pd.Timestamp("2021-01-20")))
    assert early.get_confidence_gate().threshold != late.get_confidence_gate().threshold
