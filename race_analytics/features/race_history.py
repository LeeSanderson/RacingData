import pandas as pd

_RACE_CARD_COLS = [
    "RaceId",
    "HorseId",
    "JockeyId",
    "TrainerId",
    "Surface",
    "Going",
    "RaceType",
    "DistanceInMeters",
    "WeightInPounds",
    "Class",
    "Age",
    "StallNumber",
    "Pattern",
    "RatingBand",
    "AgeBand",
    "SexRestriction",
    "HeadGear",
]


def race_card(race_history: pd.DataFrame) -> pd.DataFrame:
    """Strip an enriched race_history DataFrame to raw race-card columns only."""
    return race_history[
        [c for c in _RACE_CARD_COLS if c in race_history.columns]
    ].copy()
