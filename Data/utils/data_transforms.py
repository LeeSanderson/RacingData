import pandas as pd

surface_categories = ["Surface_AllWeather", "Surface_Dirt", "Surface_Turf"]

def encode_surfaces(races : pd.DataFrame) -> pd.DataFrame:
    races = races.drop(surface_categories + ["Surface_Unknown"], axis=1, errors='ignore')
    races["SurfaceTemp"] = races["Surface"]
    races = pd.get_dummies(races, prefix="Surface", columns=["SurfaceTemp"], dtype=float)
    races = races.drop("Surface_Unknown", axis=1) # Drop unknown surface as only small number.
    return races


going_categories  = ["Going_Good", "Going_Good_To_Soft", "Going_Soft", "Going_Good_To_Firm", "Going_Firm", "Going_Heavy"]

def encode_going(races : pd.DataFrame) -> pd.DataFrame:
    # Normalise going based on rules here: https://www.racingpost.com/guide-to-racing/what-is-the-going-ann7h6W6VB3b/
    # Values should be: Firm, Good_To_Firm, Good, Good_To_Soft, Soft, Heavy
    norm_map = ({
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
        "Frozen": "Heavy"
    })

    races["NormGoing"] = races["Going"].map(norm_map)
    races = races.drop(going_categories, axis=1, errors='ignore')
    return pd.get_dummies(races, prefix="Going", columns=["NormGoing"], dtype=float)
