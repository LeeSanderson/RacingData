import pandas as pd

_RACE_CARD_COLS = [
    "RaceId", "HorseId", "JockeyId", "TrainerId", "Surface", "Going",
    "RaceType", "DistanceInMeters", "WeightInPounds", "Class", "Age",
    "StallNumber", "Pattern", "RatingBand", "AgeBand", "SexRestriction", "HeadGear",
]


def race_card(race_history: pd.DataFrame) -> pd.DataFrame:
    """Strip an enriched race_history DataFrame to raw race-card columns only."""
    return race_history[[c for c in _RACE_CARD_COLS if c in race_history.columns]].copy()


def decompose_race_history(race_history: pd.DataFrame):
    """Decompose an enriched race_history into (races, horse_stats, jockey_stats, trainer_stats).

    trainer_stats is None when TrainerId is absent from race_history.
    """
    from race_analytics.features.horse_stats import extract_horse_stats
    from race_analytics.features.jockey_stats import extract_jockey_stats
    from race_analytics.features.trainer_stats import extract_trainer_stats
    trainer_stats = (
        extract_trainer_stats(race_history)
        if "TrainerId" in race_history.columns else None
    )
    return (
        race_card(race_history),
        extract_horse_stats(race_history),
        extract_jockey_stats(race_history),
        trainer_stats,
    )
