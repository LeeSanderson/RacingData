import pandas as pd
import pytest
from datetime import datetime

from race_analytics.algorithms.gated_classifier import GatedClassifier
from race_analytics.algorithms import GatedWinClassifier

_LONG_AGO = datetime(2020, 1, 1)
D1 = datetime(2021, 1, 1)


def _train_row(horse_id: int, race_id: int, off: datetime = D1, wins: int = 0,
               tsr: float | None = 90.0) -> dict:
    return {
        "HorseId": horse_id, "RaceId": race_id, "Off": off,
        "Wins": wins,
        "CourseName": "Newmarket",
        "Speed": 16.0, "FinishingPosition": 2, "OverallBeatenDistance": 2.0,
        "HorseCount": 8, "NumberOfPriorRaces": 3,
        "JockeyId": horse_id + 1000,
        "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
        "OfficialRating": 80.0, "RacingPostRating": 100.0, "TopSpeedRating": tsr,
        "LastRaceOfficialRating": 70.0, "LastRaceRacingPostRating": 95.0,
        "LastRaceTopSpeedRating": 92.0,
        "DistanceInMeters": 1600.0, "WeightInPounds": 126.0,
        "Surface_AllWeather": 0.0, "Surface_Dirt": 0.0, "Surface_Turf": 1.0,
        "Going_Firm": 0.0, "Going_Good": 1.0, "Going_Good_To_Firm": 0.0,
        "Going_Good_To_Soft": 0.0, "Going_Heavy": 0.0, "Going_Soft": 0.0,
        "RaceType_Flat": 1.0, "RaceType_Hurdle": 0.0,
        "RaceType_Other": 0.0, "RaceType_SteepleChase": 0.0,
        "LastRaceDistanceInMeters": 1600.0, "LastRaceWeightInPounds": 126.0,
        "LastRaceSpeed": 15.5, "DaysRested": 7.0,
        "LastRaceAvgRelFinishingPosition": 0.5,
        "LastRaceSurface_AllWeather": 0.0, "LastRaceSurface_Dirt": 0.0, "LastRaceSurface_Turf": 1.0,
        "LastRaceGoing_Good": 1.0, "LastRaceGoing_Good_To_Soft": 0.0, "LastRaceGoing_Soft": 0.0,
        "LastRaceGoing_Good_To_Firm": 0.0, "LastRaceGoing_Firm": 0.0, "LastRaceGoing_Heavy": 0.0,
        "LastRaceRaceType_Other": 0.0, "LastRaceRaceType_Hurdle": 0.0,
        "LastRaceRaceType_SteepleChase": 0.0, "LastRaceRaceType_Flat": 1.0,
        "JockeyNumberOfPriorRaces": 10.0, "DaysSinceJockeyLastRaced": 3.0,
        "JockeyWinPercentage": 0.2, "JockeyTop3Percentage": 0.5,
        "JockeyAvgRelFinishingPosition": 0.4,
    }


def _race_row(race_id: int, horse_id: int, jockey_id: int,
              distance_m: float = 1600.0, cls: str | None = None) -> dict:
    row = {
        "RaceId": race_id, "HorseId": horse_id, "JockeyId": jockey_id,
        "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
        "DistanceInMeters": distance_m, "WeightInPounds": 126.0,
    }
    if cls is not None:
        row["Class"] = cls
    return row


def _horse_stat(horse_id: int) -> dict:
    return {
        "HorseId": horse_id, "LastOff": _LONG_AGO,
        "LastRaceDistanceInMeters": 1600.0, "LastRaceWeightInPounds": 126.0,
        "LastRaceAvgRelFinishingPosition": 0.5, "LastRaceSpeed": 16.0,
        "LastRaceOfficialRating": 70.0, "LastRaceRacingPostRating": 95.0,
        "LastRaceTopSpeedRating": 92.0,
        "LastRaceSurface_AllWeather": 0.0, "LastRaceSurface_Dirt": 0.0, "LastRaceSurface_Turf": 1.0,
        "LastRaceGoing_Firm": 0.0, "LastRaceGoing_Good": 1.0,
        "LastRaceGoing_Good_To_Firm": 0.0, "LastRaceGoing_Good_To_Soft": 0.0,
        "LastRaceGoing_Heavy": 0.0, "LastRaceGoing_Soft": 0.0,
        "LastRaceRaceType_Flat": 1.0, "LastRaceRaceType_Hurdle": 0.0,
        "LastRaceRaceType_Other": 0.0, "LastRaceRaceType_SteepleChase": 0.0,
    }


def _jockey_stat(jockey_id: int) -> dict:
    return {
        "JockeyId": jockey_id, "LastOff": _LONG_AGO,
        "JockeyNumberOfPriorRaces": 10.0,
        "JockeyWinPercentage": 0.2,
        "JockeyTop3Percentage": 0.5,
        "JockeyAvgRelFinishingPosition": 0.4,
    }


def _make_train_df(n_races: int = 5) -> pd.DataFrame:
    rows = [
        _train_row(horse_id=r * 10 + h, race_id=r, off=D1, wins=1 if h == 0 else 0)
        for r in range(1, n_races + 1) for h in range(3)
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def trained_wrapper() -> GatedWinClassifier:
    algo = GatedWinClassifier(max_horses=10, coverage=0.7)
    algo.fit(_make_train_df())
    return algo


# ── 1. fit ────────────────────────────────────────────────────────────────────

def test_fit_completes_without_error():
    algo = GatedWinClassifier(max_horses=10)
    algo.fit(_make_train_df())


# ── 2. gate calibrated after fit ─────────────────────────────────────────────

def test_confidence_gate_calibrated_after_fit():
    algo = GatedWinClassifier(max_horses=10, coverage=0.7)
    algo.fit(_make_train_df())
    assert algo.get_confidence_gate()._calib_scores  # non-empty calibration


# ── 3. predict returns ["RaceId", "HorseId"] ─────────────────────────────────

def test_predict_returns_raceId_horseId_columns(trained_wrapper):
    races = pd.DataFrame([_race_row(10, h, h) for h in [101, 102, 103]])
    horse_stats = pd.DataFrame([_horse_stat(h) for h in [101, 102, 103]])
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in [101, 102, 103]])
    result = trained_wrapper.predict(races, horse_stats, jockey_stats)
    assert list(result.columns) == ["RaceId", "HorseId"]


# ── 4. coverage=0 suppresses most/all predictions ────────────────────────────

def test_lower_coverage_predicts_fewer_or_equal_races():
    """Lower coverage → higher threshold → fewer (or equal) races predicted."""
    train_df = _make_train_df(n_races=10)

    algo_full = GatedWinClassifier(max_horses=10, coverage=1.0)
    algo_full.fit(train_df)

    algo_tight = GatedWinClassifier(max_horses=10, coverage=0.3)
    algo_tight.fit(train_df)

    races = pd.DataFrame(
        [_race_row(10, h, h) for h in [101, 102, 103]]
        + [_race_row(20, h, h) for h in [201, 202, 203]]
        + [_race_row(30, h, h) for h in [301, 302, 303]]
    )
    horse_stats = pd.DataFrame([_horse_stat(h) for h in [101,102,103, 201,202,203, 301,302,303]])
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in [101,102,103, 201,202,203, 301,302,303]])

    full_preds = algo_full.predict(races, horse_stats, jockey_stats)
    tight_preds = algo_tight.predict(races, horse_stats, jockey_stats)

    assert len(tight_preds) <= len(full_preds)


# ── 5. predict_field_unfiltered >= predict_field ─────────────────────────────

def test_predict_field_unfiltered_has_at_least_as_many_rows_as_filtered(trained_wrapper):
    races = pd.DataFrame(
        [_race_row(10, h, h) for h in [101, 102, 103]]
        + [_race_row(20, h, h) for h in [201, 202, 203]]
    )
    horse_stats = pd.DataFrame([_horse_stat(h) for h in [101, 102, 103, 201, 202, 203]])
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in [101, 102, 103, 201, 202, 203]])
    filtered = trained_wrapper.predict_field(races, horse_stats, jockey_stats)
    unfiltered = trained_wrapper.predict_field_unfiltered(races, horse_stats, jockey_stats)
    assert len(unfiltered) >= len(filtered)


# ── 6. registered in ALGORITHMS list ─────────────────────────────────────────

def test_registered_in_algorithms_list():
    from race_analytics.algorithms import ALGORITHMS
    types = [type(a).__name__ for a in ALGORITHMS]
    assert "GatedWinClassifier" in types


# ── 7. Rules gate: sprint races excluded from predict_field ───────────────────

def test_sprint_race_excluded_from_predict_field(trained_wrapper):
    sprint_horses = [_race_row(99, h, h, distance_m=1000.0) for h in [901, 902, 903]]
    non_sprint_horses = [_race_row(10, h, h, distance_m=1600.0) for h in [101, 102, 103]]
    races = pd.DataFrame(sprint_horses + non_sprint_horses)
    horse_stats = pd.DataFrame([_horse_stat(h) for h in [101, 102, 103, 901, 902, 903]])
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in [101, 102, 103, 901, 902, 903]])

    result = trained_wrapper.predict_field(races, horse_stats, jockey_stats)
    assert 99 not in result["RaceId"].values


# ── 8. Rules gate: Class 6 races excluded from predict_field ─────────────────

def test_class6_race_excluded_from_predict_field(trained_wrapper):
    class6_horses = [_race_row(99, h, h, cls="Class 6") for h in [901, 902, 903]]
    normal_horses = [_race_row(10, h, h) for h in [101, 102, 103]]
    races = pd.DataFrame(class6_horses + normal_horses)
    horse_stats = pd.DataFrame([_horse_stat(h) for h in [101, 102, 103, 901, 902, 903]])
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in [101, 102, 103, 901, 902, 903]])

    result = trained_wrapper.predict_field(races, horse_stats, jockey_stats)
    assert 99 not in result["RaceId"].values


# ── 9. predict_field_unfiltered: rules gate still active ─────────────────────

def test_sprint_race_excluded_from_predict_field_unfiltered(trained_wrapper):
    sprint_horses = [_race_row(99, h, h, distance_m=1000.0) for h in [901, 902, 903]]
    non_sprint_horses = [_race_row(10, h, h, distance_m=1600.0) for h in [101, 102, 103]]
    races = pd.DataFrame(sprint_horses + non_sprint_horses)
    horse_stats = pd.DataFrame([_horse_stat(h) for h in [101, 102, 103, 901, 902, 903]])
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in [101, 102, 103, 901, 902, 903]])

    result = trained_wrapper.predict_field_unfiltered(races, horse_stats, jockey_stats)
    assert 99 not in result["RaceId"].values
