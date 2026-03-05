import pytest
import pandas as pd
import utils.test_data as td

from utils.data_transforms import (
    encode_surfaces)

@pytest.fixture
def surface_dataframe():
    race_with_unknown_surface: td.Race = td.Race(1, "Test", 2, "Test Course", td.dt("01/01/2021 12:00:00"), "Unknown")
    data = [
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown), # Surface = Turf
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.PaulTown), # Surface = AllWeather
        td.RaceResult.new(td.Wolverhampton24thAt1300, td.SecretSecret, td.PaulTown), # Surface = Dirt
        race_with_unknown_surface, # Surface = Unknown
    ]

    return pd.DataFrame(data)

def test_encode_surfaces_has_expected_columns(surface_dataframe):
    result = encode_surfaces(surface_dataframe)
    expected_columns = ["Surface_AllWeather", "Surface_Dirt", "Surface_Turf"]
    assert all(col in result.columns for col in expected_columns)

def test_encode_surfaces_has_expected_values(surface_dataframe):
    result = encode_surfaces(surface_dataframe)
    expected_values = {
        "Surface_AllWeather": [0.0, 1.0, 0.0, 0.0],
        "Surface_Dirt": [0.0, 0.0, 1.0, 0.0],
        "Surface_Turf": [1.0, 0.0, 0.0, 0.0],
    }
    for col, expected in expected_values.items():
        assert result[col].tolist() == expected

def test_encode_surfaces_drops_unknown_surface(surface_dataframe):
    result = encode_surfaces(surface_dataframe)
    assert "Surface_Unknown" not in result.columns
