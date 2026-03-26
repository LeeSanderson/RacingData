import pytest
import pandas as pd
import utils.test_data as td

from utils.data_transforms import (
    encode_surfaces,
    encode_going,
    calculate_speed,
    clean_weight,
    calculate_horse_count,
)

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


@pytest.fixture
def going_dataframe():
    """Test fixture with various going conditions"""
    data = [
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown, "Good"),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.PaulTown, "Soft"),
        td.RaceResult.new(td.Wolverhampton24thAt1300, td.SecretSecret, td.PaulTown, "Good To Firm"),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.SecretSecret, td.PaulTown, "Heavy"),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown, "Good To Soft"),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.PaulTown, "Firm"),
    ]
    return pd.DataFrame(data)

def test_encode_going_has_expected_columns(going_dataframe):
    """Test that encode_going creates the expected columns for data that exists"""
    result = encode_going(going_dataframe)

    # Should have Going_ prefixed columns for categories that exist in the test data
    # Test data has: Good, Soft, Good To Firm, Heavy, Good To Soft, Firm
    expected_columns = ["Going_Good", "Going_Good_To_Soft", "Going_Soft", "Going_Good_To_Firm", "Going_Firm", "Going_Heavy"]

    for col in expected_columns:
        assert col in result.columns, f"Expected column {col} should exist"
        assert result[col].dtype == float, f"Column {col} should be float type"


def test_encode_going_standard_values(going_dataframe):
    """Test that standard going conditions are encoded correctly"""
    result = encode_going(going_dataframe)

    # Check first row (Good)
    assert result.iloc[0]["Going_Good"] == 1.0
    assert result.iloc[0]["Going_Soft"] == 0.0
    assert result.iloc[0]["Going_Good_To_Firm"] == 0.0
    assert result.iloc[0]["Going_Heavy"] == 0.0
    assert result.iloc[0]["Going_Good_To_Soft"] == 0.0
    assert result.iloc[0]["Going_Firm"] == 0.0

    # Check second row (Soft)
    assert result.iloc[1]["Going_Soft"] == 1.0
    assert result.iloc[1]["Going_Good"] == 0.0

    # Check third row (Good To Firm)
    assert result.iloc[2]["Going_Good_To_Firm"] == 1.0
    assert result.iloc[2]["Going_Good"] == 0.0


@pytest.fixture
def going_normalization_dataframe():
    """Test fixture with going conditions that need normalization"""
    data = [
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown, "Standard"),  # -> Good
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.PaulTown, "Yielding"),  # -> Good_To_Soft
        td.RaceResult.new(td.Wolverhampton24thAt1300, td.SecretSecret, td.PaulTown, "Fast"),   # -> Firm
        td.RaceResult.new(td.Nottingham22ndAt1815, td.SecretSecret, td.PaulTown, "Very Soft"), # -> Heavy
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown, "Good To Yielding"), # -> Good_To_Soft
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.PaulTown, "Muddy"),     # -> Heavy
        td.RaceResult.new(td.Wolverhampton24thAt1300, td.SecretSecret, td.PaulTown, "Slow"),   # -> Soft
    ]
    return pd.DataFrame(data)

def test_encode_going_normalization_mapping(going_normalization_dataframe):
    """Test that various going conditions are normalized to standard categories"""
    result = encode_going(going_normalization_dataframe)

    expected_values = [
        ("Going_Good", 0),        # Standard -> Good
        ("Going_Good_To_Soft", 1), # Yielding -> Good_To_Soft
        ("Going_Firm", 2),        # Fast -> Firm
        ("Going_Heavy", 3),       # Very Soft -> Heavy
        ("Going_Good_To_Soft", 4), # Good To Yielding -> Good_To_Soft
        ("Going_Heavy", 5),       # Muddy -> Heavy
        ("Going_Soft", 6),        # Slow -> Soft
    ]

    for expected_col, row_idx in expected_values:
        # Check that the expected column exists and is 1.0 for this row
        assert expected_col in result.columns, f"Column {expected_col} should exist"
        assert result.iloc[row_idx][expected_col] == 1.0, f"Row {row_idx} should have {expected_col} = 1.0"

        # Check that all other going columns are 0.0 for this row
        all_going_cols = [col for col in result.columns if col.startswith("Going_")]
        other_cols = [col for col in all_going_cols if col != expected_col]
        for col in other_cols:
            assert result.iloc[row_idx][col] == 0.0, f"Row {row_idx} should have {col} = 0.0"


def test_encode_going_drops_existing_going_columns():
    """Test that existing going columns are dropped before encoding"""
    # Create dataframe with existing Going_ columns
    data = [
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown, "Good"),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.PaulTown, "Soft"),
    ]
    df = pd.DataFrame(data)

    # Add existing going columns
    df["Going_Good"] = [0.5, 0.3]  # Some existing values
    df["Going_Soft"] = [0.2, 0.7]

    result = encode_going(df)

    # Check that the function creates proper one-hot encoding despite existing columns
    assert result.iloc[0]["Going_Good"] == 1.0
    assert result.iloc[0]["Going_Soft"] == 0.0
    assert result.iloc[1]["Going_Good"] == 0.0
    assert result.iloc[1]["Going_Soft"] == 1.0


def test_encode_going_preserves_other_columns(going_dataframe):
    """Test that non-going columns are preserved"""
    result = encode_going(going_dataframe)

    # Check that original Going column is preserved (not dropped by the function)
    assert "Going" in result.columns
    # Check that NormGoing column is created but then used for dummy variables
    assert "NormGoing" not in result.columns  # Should be consumed by get_dummies


def test_encode_going_handles_unknown_conditions():
    """Test behavior with going conditions not in the normalization map"""
    data = [
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown, "Unknown Going"),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.PaulTown, "Good"),
    ]
    df = pd.DataFrame(data)

    result = encode_going(df)

    # Find all Going_ columns
    going_cols = [col for col in result.columns if col.startswith("Going_")]

    # Unknown going should result in NaN which becomes 0.0 in all going columns for that row
    for col in going_cols:
        assert result.iloc[0][col] == 0.0, f"Unknown going should result in {col} = 0.0"

    # Second row (Good) should have exactly one going column as 1.0
    going_values = [result.iloc[1][col] for col in going_cols]
    assert sum(going_values) == 1.0, "Exactly one going column should be 1.0 for valid going"
    assert result.iloc[1]["Going_Good"] == 1.0, "Good going should set Going_Good = 1.0"


# --- calculate_speed ---

@pytest.fixture
def speed_dataframe():
    return pd.DataFrame({
        "DistanceInMeters": [1600, 2000, 1200, 800],
        "RaceTimeInSeconds": [100.0, 125.0, 60.0, 38.0],  # speeds: 16, 16, 20, ~21.05
    })


def test_calculate_speed_adds_speed_column(speed_dataframe):
    result = calculate_speed(speed_dataframe)
    assert "Speed" in result.columns


def test_calculate_speed_calculates_correctly(speed_dataframe):
    result = calculate_speed(speed_dataframe)
    assert result.iloc[0]["Speed"] == pytest.approx(16.0)
    assert result.iloc[1]["Speed"] == pytest.approx(16.0)


def test_calculate_speed_clamps_over_20_to_nan(speed_dataframe):
    result = calculate_speed(speed_dataframe)
    # Row 3 has speed ~21.05 > 20, should be NaN
    assert pd.isna(result.iloc[3]["Speed"])


def test_calculate_speed_preserves_exactly_20(speed_dataframe):
    result = calculate_speed(speed_dataframe)
    # Row 2 has speed exactly 20, should be preserved
    assert result.iloc[2]["Speed"] == pytest.approx(20.0)


# --- clean_weight ---

@pytest.fixture
def weight_dataframe():
    return pd.DataFrame({
        "WeightInPounds": [126.0, 9.0, 0.0, 130.0, 10.0],
    })


def test_clean_weight_sets_invalid_to_nan(weight_dataframe):
    result = clean_weight(weight_dataframe)
    assert pd.isna(result.iloc[1]["WeightInPounds"])  # 9.0 < 10
    assert pd.isna(result.iloc[2]["WeightInPounds"])  # 0.0 < 10


def test_clean_weight_preserves_valid_weights(weight_dataframe):
    result = clean_weight(weight_dataframe)
    assert result.iloc[0]["WeightInPounds"] == 126.0
    assert result.iloc[3]["WeightInPounds"] == 130.0


def test_clean_weight_preserves_boundary_value(weight_dataframe):
    result = clean_weight(weight_dataframe)
    # Exactly 10 is valid (condition is < 10)
    assert result.iloc[4]["WeightInPounds"] == 10.0


# --- calculate_horse_count ---

@pytest.fixture
def horse_count_dataframe():
    return pd.DataFrame([
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.DuckAndVanish, td.PhilipDonovan),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.LaylaDaffodil, td.ShaneFitzgerald),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.DuckAndVanish, td.PhilipDonovan),
    ])


def test_calculate_horse_count_adds_column(horse_count_dataframe):
    result = calculate_horse_count(horse_count_dataframe)
    assert "HorseCount" in result.columns


def test_calculate_horse_count_correct_counts(horse_count_dataframe):
    result = calculate_horse_count(horse_count_dataframe)
    ballinrobe_rows = result[result["RaceId"] == td.Ballinrobe20thAt1515.RaceId]
    chelmsford_rows = result[result["RaceId"] == td.Chelmsford21stAt1805.RaceId]
    assert (ballinrobe_rows["HorseCount"] == 3).all()
    assert (chelmsford_rows["HorseCount"] == 2).all()


def test_calculate_horse_count_preserves_row_count(horse_count_dataframe):
    result = calculate_horse_count(horse_count_dataframe)
    assert len(result) == len(horse_count_dataframe)
