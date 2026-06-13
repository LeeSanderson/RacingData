import pandas as pd
from datetime import datetime

from race_analytics.features.race_history import race_card

_RACE_CARD_COLS = [
    "RaceId", "HorseId", "JockeyId", "TrainerId", "Surface", "Going",
    "RaceType", "DistanceInMeters", "WeightInPounds", "Class", "Age",
    "StallNumber", "Pattern", "RatingBand", "AgeBand", "SexRestriction", "HeadGear",
]

D1 = datetime(2021, 1, 1)


def _enriched_row(horse_id: int, race_id: int, off: datetime = D1) -> dict:
    return {
        "HorseId": horse_id, "RaceId": race_id, "Off": off,
        "JockeyId": horse_id + 1000, "TrainerId": horse_id + 2000,
        "Surface": "Turf", "Going": "Good", "RaceType": "Flat",
        "DistanceInMeters": 1600.0, "WeightInPounds": 126.0,
        "Class": "Class 3", "Age": 4,
        "StallNumber": 1, "Pattern": None, "RatingBand": None,
        "AgeBand": "4yo+", "SexRestriction": None, "HeadGear": None,
        "Wins": 0, "Speed": 16.0, "FinishingPosition": 2,
        "OverallBeatenDistance": 2.0, "HorseCount": 8,
        "OfficialRating": 80.0, "RacingPostRating": 100.0, "TopSpeedRating": 90.0,
        "LastRaceOfficialRating": 70.0, "LastRaceRacingPostRating": 95.0,
        "LastRaceTopSpeedRating": 92.0,
        "NumberOfPriorRaces": 3,
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
        "TrainerNumberOfPriorRaces": 20.0, "DaysSinceTrainerLastRaced": 2.0,
        "TrainerWinPercentage": 0.15, "TrainerTop3Percentage": 0.4,
        "TrainerAvgRelFinishingPosition": 0.45,
    }


def _make_enriched_df(n_races: int = 3) -> pd.DataFrame:
    rows = [
        _enriched_row(horse_id=r * 10 + h, race_id=r, off=D1)
        for r in range(1, n_races + 1) for h in range(3)
    ]
    return pd.DataFrame(rows)


# ── race_card ─────────────────────────────────────────────────────────────────

def test_race_card_returns_only_card_columns():
    df = _make_enriched_df()
    result = race_card(df)
    for col in result.columns:
        assert col in _RACE_CARD_COLS, f"unexpected column: {col}"


def test_race_card_includes_present_card_columns():
    df = _make_enriched_df()
    result = race_card(df)
    for col in ["RaceId", "HorseId", "Surface", "Going", "RaceType", "DistanceInMeters"]:
        assert col in result.columns, f"missing expected card column: {col}"


def test_race_card_excludes_feature_columns():
    df = _make_enriched_df()
    result = race_card(df)
    for col in ["LastRaceSpeed", "DaysRested", "JockeyWinPercentage", "Speed"]:
        assert col not in result.columns, f"feature column leaked into card: {col}"
