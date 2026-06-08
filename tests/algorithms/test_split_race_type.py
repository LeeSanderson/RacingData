import pandas as pd
from datetime import datetime

_LONG_AGO = datetime(2020, 1, 1)
D1 = datetime(2021, 1, 1)


def _train_row(
    horse_id: int,
    race_id: int,
    race_type_flat: float = 1.0,
    wins: int = 0,
    finishing_position: int = 2,
) -> dict:
    is_flat = race_type_flat == 1.0
    return {
        "HorseId": horse_id, "RaceId": race_id, "Off": D1,
        "Wins": wins, "FinishingPosition": finishing_position,
        "CourseName": "Newmarket",
        "Speed": 16.0, "OverallBeatenDistance": 2.0, "HorseCount": 8,
        "OfficialRating": 80.0, "RacingPostRating": 100.0, "TopSpeedRating": 90.0,
        "LastRaceOfficialRating": 70.0, "LastRaceRacingPostRating": 95.0,
        "LastRaceTopSpeedRating": 92.0,
        "DistanceInMeters": 1600.0, "WeightInPounds": 126.0,
        "Surface_AllWeather": 0.0, "Surface_Dirt": 0.0, "Surface_Turf": 1.0,
        "Going_Firm": 0.0, "Going_Good": 1.0, "Going_Good_To_Firm": 0.0,
        "Going_Good_To_Soft": 0.0, "Going_Heavy": 0.0, "Going_Soft": 0.0,
        "RaceType_Flat": race_type_flat, "RaceType_Hurdle": 0.0 if is_flat else 1.0,
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


def _race_row(race_id: int, horse_id: int, jockey_id: int, race_type: str = "Flat") -> dict:
    return {
        "RaceId": race_id, "HorseId": horse_id, "JockeyId": jockey_id,
        "Surface": "Turf", "Going": "Good", "RaceType": race_type,
        "DistanceInMeters": 1600.0, "WeightInPounds": 126.0,
        "OfficialRating": 80.0, "RacingPostRating": 100.0, "TopSpeedRating": 90.0,
    }


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


def _make_train_df(n_flat: int = 110, n_jumps: int = 110) -> pd.DataFrame:
    """Generate training data with n_flat flat races and n_jumps hurdle races."""
    rows = []
    for i in range(n_flat):
        race_id = i + 1
        for h in range(4):
            rows.append(_train_row(horse_id=race_id * 10 + h, race_id=race_id,
                                   race_type_flat=1.0, wins=1 if h == 0 else 0,
                                   finishing_position=h + 1))
    for i in range(n_jumps):
        race_id = n_flat + i + 1
        for h in range(4):
            rows.append(_train_row(horse_id=race_id * 10 + h, race_id=race_id,
                                   race_type_flat=0.0, wins=1 if h == 0 else 0,
                                   finishing_position=h + 1))
    return pd.DataFrame(rows)


def test_split_and_abstain_registered_in_algorithms():
    from race_analytics.algorithms import ALGORITHMS
    names = [type(a).__name__ for a in ALGORITHMS]
    assert "SplitDisciplineWinClassifier" in names
    assert "GatedSplitDisciplineWinClassifier" in names


def test_flat_model_available_with_sufficient_flat_races():
    from race_analytics.algorithms.split_discipline_win_classifier import SplitDisciplineWinClassifier

    algo = SplitDisciplineWinClassifier(max_horses=10)
    algo.fit(_make_train_df(n_flat=110, n_jumps=110))

    assert algo._flat_available
    assert algo._jumps_available


def test_flat_races_route_to_flat_model_predict_field():
    from race_analytics.algorithms.split_discipline_win_classifier import SplitDisciplineWinClassifier

    algo = SplitDisciplineWinClassifier(max_horses=10)
    algo.fit(_make_train_df(n_flat=110, n_jumps=110))

    races = pd.DataFrame([_race_row(500, h, h, race_type="Flat") for h in [1001, 1002, 1003]])
    horse_stats = pd.DataFrame([_horse_stat(h) for h in [1001, 1002, 1003]])
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in [1001, 1002, 1003]])

    result = algo.predict_field(races, horse_stats, jockey_stats)

    assert not result.empty
    for col in ["RaceId", "HorseId", "WinProbability", "PredictedRank"]:
        assert col in result.columns, f"missing column: {col}"


def test_fallback_used_when_flat_has_insufficient_races():
    from race_analytics.algorithms.split_discipline_win_classifier import SplitDisciplineWinClassifier

    # Only 5 flat races — below MIN_RACES threshold
    algo = SplitDisciplineWinClassifier(max_horses=10)
    algo.fit(_make_train_df(n_flat=5, n_jumps=110))

    assert not algo._flat_available
    assert algo._jumps_available

    # Predictions on flat races must still work (fallback used, no drops)
    races = pd.DataFrame([_race_row(500, h, h, race_type="Flat") for h in [1001, 1002, 1003]])
    horse_stats = pd.DataFrame([_horse_stat(h) for h in [1001, 1002, 1003]])
    jockey_stats = pd.DataFrame([_jockey_stat(h) for h in [1001, 1002, 1003]])

    result = algo.predict_field(races, horse_stats, jockey_stats)

    assert not result.empty
    assert "WinProbability" in result.columns


def test_inner_class_param_accepts_recency_weighted():
    from race_analytics.algorithms.split_discipline_win_classifier import SplitDisciplineWinClassifier
    from race_analytics.algorithms.recency_weighted_win_classifier import RecencyWeightedWinClassifier

    algo = SplitDisciplineWinClassifier(inner_class=RecencyWeightedWinClassifier, max_horses=10)
    algo.fit(_make_train_df(n_flat=110, n_jumps=110))

    assert isinstance(algo._flat_model, RecencyWeightedWinClassifier)
    assert isinstance(algo._jumps_model, RecencyWeightedWinClassifier)
    assert isinstance(algo._fallback_model, RecencyWeightedWinClassifier)
