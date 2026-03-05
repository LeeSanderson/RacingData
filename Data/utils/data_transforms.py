import pandas as pd

surface_categories = ["Surface_AllWeather", "Surface_Dirt", "Surface_Turf"]

def encode_surfaces(races : pd.DataFrame) -> pd.DataFrame:
    races = races.drop(surface_categories + ["Surface_Unknown"], axis=1, errors='ignore')
    races["SurfaceTemp"] = races["Surface"]
    races = pd.get_dummies(races, prefix="Surface", columns=["SurfaceTemp"], dtype=float)
    races = races.drop("Surface_Unknown", axis=1) # Drop unknown surface as only small number.
    return races
