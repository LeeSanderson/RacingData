import numpy as np
import pandas as pd

surface_categories = ["Surface_AllWeather", "Surface_Dirt", "Surface_Turf"]


def encode_surfaces(races: pd.DataFrame) -> pd.DataFrame:
    races = races.drop(
        surface_categories + ["Surface_Unknown"], axis=1, errors="ignore"
    )
    races["SurfaceTemp"] = races["Surface"]
    races = pd.get_dummies(
        races, prefix="Surface", columns=["SurfaceTemp"], dtype=float
    )
    races = races.drop(
        "Surface_Unknown", axis=1, errors="ignore"
    )  # Drop unknown surface as only small number.
    for col in surface_categories:
        if col not in races.columns:
            races[col] = 0.0
    return races


going_categories = [
    "Going_Good",
    "Going_Good_To_Soft",
    "Going_Soft",
    "Going_Good_To_Firm",
    "Going_Firm",
    "Going_Heavy",
]


def encode_going(races: pd.DataFrame) -> pd.DataFrame:
    # Normalise going based on rules here: https://www.racingpost.com/guide-to-racing/what-is-the-going-ann7h6W6VB3b/
    # Values should be: Firm, Good_To_Firm, Good, Good_To_Soft, Soft, Heavy
    norm_map = {
        "Good": "Good",
        "Standard": "Good",
        "Soft": "Soft",
        "Good To Soft": "Good_To_Soft",
        "Good To Firm": "Good_To_Firm",
        "Heavy": "Heavy",
        "Good To Yielding": "Good_To_Soft",
        "Yielding": "Good_To_Soft",
        "Standard To Slow": "Good_To_Soft",
        "Very Soft": "Heavy",
        "Fast": "Firm",
        "Firm": "Firm",
        "Soft To Heavy": "Heavy",
        "Yielding To Soft": "Soft",
        "Slow": "Soft",
        "Sloppy": "Heavy",
        "Muddy": "Heavy",
        "Frozen": "Heavy",
    }

    races["NormGoing"] = races["Going"].map(norm_map)
    races = races.drop(going_categories, axis=1, errors="ignore")
    races = pd.get_dummies(races, prefix="Going", columns=["NormGoing"], dtype=float)
    for col in going_categories:
        if col not in races.columns:
            races[col] = 0.0
    return races


race_type_categories = [
    "RaceType_Other",
    "RaceType_Hurdle",
    "RaceType_SteepleChase",
    "RaceType_Flat",
]


def encode_race_type(races: pd.DataFrame) -> pd.DataFrame:
    races = races.drop(race_type_categories, axis=1, errors="ignore")
    races["RaceTypeTemp"] = races["RaceType"]
    races = pd.get_dummies(
        races, prefix="RaceType", columns=["RaceTypeTemp"], dtype=float
    )
    for col in race_type_categories:
        if col not in races.columns:
            races[col] = 0.0
    return races


def calculate_speed(races: pd.DataFrame) -> pd.DataFrame:
    races["Speed"] = races["DistanceInMeters"] / races["RaceTimeInSeconds"]
    # Clamp invalid speeds (usually due to invalid race time) - fastest horses are ~20 m/s
    races.loc[races["Speed"] > 20, "Speed"] = np.nan
    return races


def clean_weight(races: pd.DataFrame) -> pd.DataFrame:
    # Occasionally weight will be undefined (usually zero)
    races.loc[races["WeightInPounds"] < 10, "WeightInPounds"] = np.nan
    return races


def calculate_horse_count(races: pd.DataFrame) -> pd.DataFrame:
    groups = (
        races.groupby(["RaceId"])["HorseId"]
        .agg(["count"])
        .rename(columns={"count": "HorseCount"})
    )
    return pd.merge(races, groups, how="left", on=["RaceId"])
