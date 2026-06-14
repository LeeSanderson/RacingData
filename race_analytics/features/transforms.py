from typing import Any

import numpy as np
import pandas as pd

surface_categories = ["Surface_AllWeather", "Surface_Dirt", "Surface_Turf"]


def encode_surfaces(races: pd.DataFrame) -> pd.DataFrame:
    races = races.drop(
        [*surface_categories, "Surface_Unknown"], axis=1, errors="ignore"
    )
    races["SurfaceTemp"] = races["Surface"]
    races = pd.get_dummies(
        races, prefix="Surface", columns=["SurfaceTemp"], dtype=float
    )
    races = races.drop("Surface_Unknown", axis=1, errors="ignore")
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

    # Empty or null going defaults to "Good" — the most common condition for UK racing.
    races["NormGoing"] = races["Going"].fillna("Good").replace("", "Good").map(norm_map)
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
        .rename(columns={"count": "HorseCount"})  # pyright: ignore[reportCallIssue]  # rename(columns=) overload gap
    )
    return races.merge(groups, how="left", on=["RaceId"])


calculateHorsesPerRace = calculate_horse_count


def calculate_weight_change(races: pd.DataFrame) -> pd.DataFrame:
    if (
        "WeightInPounds" not in races.columns
        or "LastRaceWeightInPounds" not in races.columns
    ):
        races["WeightChange"] = np.nan
        return races
    races["WeightChange"] = races["WeightInPounds"] - races["LastRaceWeightInPounds"]
    return races


def calculate_distance_change(races: pd.DataFrame) -> pd.DataFrame:
    if (
        "DistanceInMeters" not in races.columns
        or "LastRaceDistanceInMeters" not in races.columns
    ):
        races["DistanceChange"] = np.nan
        return races
    races["DistanceChange"] = (
        races["DistanceInMeters"] - races["LastRaceDistanceInMeters"]
    )
    return races


def calculate_surface_switch(races: pd.DataFrame) -> pd.DataFrame:
    last_cols = [f"LastRace{c}" for c in surface_categories]
    if not all(c in races.columns for c in last_cols):
        races["SurfaceSwitch"] = np.nan
        return races
    has_last = races[last_cols].notna().any(axis=1)
    current = races[list(surface_categories)].fillna(0.0).values
    last = races[last_cols].fillna(0.0).values
    same = (current * last).sum(axis=1)
    races["SurfaceSwitch"] = np.where(has_last, 1.0 - same, np.nan)
    return races


def calculate_code_switch(races: pd.DataFrame) -> pd.DataFrame:
    last_rt_cols = [f"LastRace{c}" for c in race_type_categories]
    if not all(c in races.columns for c in last_rt_cols):
        races["CodeSwitch"] = np.nan
        return races
    has_last = races[last_rt_cols].notna().any(axis=1)
    current_is_flat = races["RaceType_Flat"] == 1.0
    last_is_flat = races["LastRaceRaceType_Flat"] == 1.0
    switch = (current_is_flat ^ last_is_flat).astype(float)
    races["CodeSwitch"] = np.where(has_last, switch, np.nan)
    return races


pattern_categories = [
    "Pattern_Group1",
    "Pattern_Group2",
    "Pattern_Group3",
    "Pattern_Listed",
    "Pattern_None",
]

age_band_categories = [
    "AgeBand_2yo",
    "AgeBand_3yo",
    "AgeBand_3yoPlus",
    "AgeBand_4yoPlus",
    "AgeBand_None",
]

sex_restriction_categories = [
    "SexRestriction_F",
    "SexRestriction_FM",
    "SexRestriction_Open",
]


def calculate_race_class(races: pd.DataFrame) -> pd.DataFrame:
    if "Class" not in races.columns:
        races["RaceClass"] = np.nan
        return races

    def _parse(v: Any) -> float:
        try:
            i = int(str(v).strip())
            return float(i) if 1 <= i <= 7 else 0.0
        except (ValueError, TypeError):
            return 0.0

    races["RaceClass"] = races["Class"].apply(_parse)
    return races


def calculate_age_features(races: pd.DataFrame) -> pd.DataFrame:
    if "Age" not in races.columns:
        races["Age"] = np.nan
        races["RelAge"] = np.nan
        return races
    ages = pd.to_numeric(races["Age"], errors="coerce")
    races["Age"] = ages
    if "RaceId" in races.columns:
        mean_age = races.groupby("RaceId")["Age"].transform("mean")
        races["RelAge"] = ages - mean_age
    else:
        races["RelAge"] = np.nan
    return races


def calculate_draw_features(races: pd.DataFrame) -> pd.DataFrame:
    if "StallNumber" not in races.columns or "HorseCount" not in races.columns:
        races["DrawPct"] = np.nan
        races["RelDraw"] = np.nan
        return races
    stall = pd.to_numeric(races["StallNumber"], errors="coerce")
    is_flat = (
        races["RaceType_Flat"] == 1.0
        if "RaceType_Flat" in races.columns
        else pd.Series(False, index=races.index)
    )
    count = races["HorseCount"]
    valid = is_flat & stall.notna() & (count > 0)  # pyright: ignore[reportAttributeAccessIssue]  # to_numeric returns a Series
    draw_pct = pd.Series(np.nan, index=races.index, dtype=float)
    draw_pct[valid] = stall[valid] / count[valid]  # pyright: ignore[reportIndexIssue]  # Series supports boolean-mask indexing
    races["DrawPct"] = draw_pct
    races["RelDraw"] = draw_pct - 0.5
    return races


def encode_pattern(races: pd.DataFrame) -> pd.DataFrame:
    races = races.drop(pattern_categories, axis=1, errors="ignore")
    if "Pattern" not in races.columns:
        for col in pattern_categories:
            races[col] = 0.0
        return races
    _norm = {
        "Group 1": "Group1",
        "G1": "Group1",
        "Grade 1": "Group1",
        "Group 2": "Group2",
        "G2": "Group2",
        "Grade 2": "Group2",
        "Group 3": "Group3",
        "G3": "Group3",
        "Grade 3": "Group3",
        "Listed": "Listed",
        "L": "Listed",
    }
    normalized = (
        races["Pattern"].fillna("").astype(str).str.strip().map(_norm).fillna("None")
    )
    dummies = pd.get_dummies(
        pd.DataFrame({"PatternTemp": normalized}),
        prefix="Pattern",
        columns=["PatternTemp"],
        dtype=float,
    )
    for col in pattern_categories:
        races[col] = dummies.get(col, pd.Series(0.0, index=races.index))
    return races


def calculate_is_handicap(races: pd.DataFrame) -> pd.DataFrame:
    if "RatingBand" not in races.columns:
        races["IsHandicap"] = np.nan
        return races
    has_band = races["RatingBand"].notna() & (
        races["RatingBand"].astype(str).str.strip() != ""
    )
    races["IsHandicap"] = has_band.astype(float)
    return races


def encode_age_band(races: pd.DataFrame) -> pd.DataFrame:
    races = races.drop(age_band_categories, axis=1, errors="ignore")
    if "AgeBand" not in races.columns:
        for col in age_band_categories:
            races[col] = 0.0
        races["AgeBand_None"] = 1.0
        return races
    _norm = {
        "2yo": "2yo",
        "3yo": "3yo",
        "3yo+": "3yoPlus",
        "3+": "3yoPlus",
        "3yo -": "3yoPlus",
        "4yo+": "4yoPlus",
        "4+": "4yoPlus",
        "5yo+": "4yoPlus",
        "5+": "4yoPlus",
        "6yo+": "4yoPlus",
    }
    normalized = (
        races["AgeBand"].fillna("").astype(str).str.strip().map(_norm).fillna("None")
    )
    dummies = pd.get_dummies(
        pd.DataFrame({"AgeBandTemp": normalized}),
        prefix="AgeBand",
        columns=["AgeBandTemp"],
        dtype=float,
    )
    for col in age_band_categories:
        races[col] = dummies.get(col, pd.Series(0.0, index=races.index))
    return races


headgear_columns = [
    "IsFirstTimeHeadgear",
    "HasBlinkers",
    "HasCheekpieces",
    "HasTongueTie",
    "HasHood",
    "HasVisor",
    "HeadGearChanged",
]


def encode_headgear(races: pd.DataFrame) -> pd.DataFrame:
    races = races.drop(headgear_columns, axis=1, errors="ignore")
    codes = (
        races["HeadGear"].fillna("").astype(str)
        if "HeadGear" in races.columns
        else pd.Series("", index=races.index)
    )
    races["IsFirstTimeHeadgear"] = codes.str.endswith("1").astype(float)
    base = codes.str.rstrip("1")
    races["HasBlinkers"] = base.str.contains("b", regex=False).astype(float)
    races["HasCheekpieces"] = base.str.contains("p", regex=False).astype(float)
    races["HasTongueTie"] = base.str.contains("t", regex=False).astype(float)
    races["HasHood"] = base.str.contains("h", regex=False).astype(float)
    races["HasVisor"] = base.str.contains("v", regex=False).astype(float)
    if "LastRaceHeadGear" in races.columns:
        last = races["LastRaceHeadGear"].fillna("").astype(str)
        both_empty = (codes == "") & (last == "")
        races["HeadGearChanged"] = np.where(
            both_empty, 0.0, (codes != last).astype(float)
        )
    else:
        races["HeadGearChanged"] = 0.0
    return races


def encode_sex_restriction(races: pd.DataFrame) -> pd.DataFrame:
    races = races.drop(sex_restriction_categories, axis=1, errors="ignore")
    if "SexRestriction" not in races.columns:
        for col in sex_restriction_categories:
            races[col] = 0.0
        races["SexRestriction_Open"] = 1.0
        return races
    _norm = {
        "F": "F",
        "Fillies": "F",
        "Fillies Only": "F",
        "M": "FM",
        "Mares": "FM",
        "Mares Only": "FM",
        "F&M": "FM",
        "Fillies & Mares": "FM",
        "Fillies and Mares": "FM",
    }
    normalized = (
        races["SexRestriction"]
        .fillna("")
        .astype(str)
        .str.strip()
        .map(_norm)
        .fillna("Open")
    )
    dummies = pd.get_dummies(
        pd.DataFrame({"SexTemp": normalized}),
        prefix="SexRestriction",
        columns=["SexTemp"],
        dtype=float,
    )
    for col in sex_restriction_categories:
        races[col] = dummies.get(col, pd.Series(0.0, index=races.index))
    return races
