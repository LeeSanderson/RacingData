import pytest
import pandas as pd
import tests.utils.test_data as td

from race_analytics.features.transforms import (
    surface_categories,
    going_categories,
    race_type_categories,
    encode_surfaces,
    encode_going,
    encode_race_type,
    calculate_speed,
    clean_weight,
    calculate_horse_count,
    calculate_weight_change,
    calculate_distance_change,
)


# --- encode_surfaces ---


@pytest.fixture
def surface_dataframe():
    race_with_unknown_surface = td.Race(
        1, "Test", 2, "Test Course", td.dt("01/01/2021 12:00:00"), "Unknown"
    )
    data = [
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown),  # Turf
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.PaulTown),  # AllWeather
        td.RaceResult.new(td.Wolverhampton24thAt1300, td.SecretSecret, td.PaulTown),  # Dirt
        race_with_unknown_surface,
    ]
    return pd.DataFrame(data)


def test_encode_surfaces_has_expected_columns(surface_dataframe):
    result = encode_surfaces(surface_dataframe)
    assert all(col in result.columns for col in surface_categories)


def test_encode_surfaces_has_expected_values(surface_dataframe):
    result = encode_surfaces(surface_dataframe)
    expected = {
        "Surface_AllWeather": [0.0, 1.0, 0.0, 0.0],
        "Surface_Dirt": [0.0, 0.0, 1.0, 0.0],
        "Surface_Turf": [1.0, 0.0, 0.0, 0.0],
    }
    for col, values in expected.items():
        assert result[col].tolist() == values


def test_encode_surfaces_drops_unknown_surface(surface_dataframe):
    result = encode_surfaces(surface_dataframe)
    assert "Surface_Unknown" not in result.columns


# --- encode_going ---


@pytest.fixture
def going_dataframe():
    data = [
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown, "Good"),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.PaulTown, "Soft"),
        td.RaceResult.new(td.Wolverhampton24thAt1300, td.SecretSecret, td.PaulTown, "Good To Firm"),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.SecretSecret, td.PaulTown, "Heavy"),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown, "Good To Soft"),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.PaulTown, "Firm"),
    ]
    return pd.DataFrame(data)


def test_encode_going_has_all_six_categories(going_dataframe):
    result = encode_going(going_dataframe)
    for col in going_categories:
        assert col in result.columns
        assert result[col].dtype == float


def test_encode_going_standard_values(going_dataframe):
    result = encode_going(going_dataframe)
    assert result.iloc[0]["Going_Good"] == 1.0
    assert result.iloc[1]["Going_Soft"] == 1.0
    assert result.iloc[2]["Going_Good_To_Firm"] == 1.0
    assert result.iloc[3]["Going_Heavy"] == 1.0
    assert result.iloc[4]["Going_Good_To_Soft"] == 1.0
    assert result.iloc[5]["Going_Firm"] == 1.0


def test_encode_going_unknown_string_gives_all_zeros():
    data = [
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown, "Unknown Going"),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.PaulTown, "Good"),
    ]
    df = pd.DataFrame(data)
    result = encode_going(df)
    going_cols = [c for c in result.columns if c.startswith("Going_")]
    for col in going_cols:
        assert result.iloc[0][col] == 0.0


def test_encode_going_defaults_empty_to_good():
    data = [
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown, ""),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.PaulTown, "Soft"),
    ]
    df = pd.DataFrame(data)
    result = encode_going(df)
    assert result.iloc[0]["Going_Good"] == 1.0
    for col in going_categories:
        if col != "Going_Good":
            assert result.iloc[0][col] == 0.0


# --- encode_race_type ---


@pytest.fixture
def race_type_dataframe():
    return pd.DataFrame({
        "RaceType": ["Hurdle", "Flat", "SteepleChase", "Other"],
    })


def test_encode_race_type_has_all_four_categories(race_type_dataframe):
    result = encode_race_type(race_type_dataframe)
    for col in race_type_categories:
        assert col in result.columns


def test_encode_race_type_values(race_type_dataframe):
    result = encode_race_type(race_type_dataframe)
    assert result.iloc[0]["RaceType_Hurdle"] == 1.0
    assert result.iloc[1]["RaceType_Flat"] == 1.0
    assert result.iloc[2]["RaceType_SteepleChase"] == 1.0
    assert result.iloc[3]["RaceType_Other"] == 1.0


def test_encode_race_type_unknown_produces_all_zeros():
    df = pd.DataFrame({"RaceType": ["Chase", "Flat"]})
    result = encode_race_type(df)
    for col in race_type_categories:
        assert col in result.columns
        assert result.iloc[0][col] == 0.0


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
    assert pd.isna(result.iloc[3]["Speed"])


def test_calculate_speed_preserves_exactly_20(speed_dataframe):
    result = calculate_speed(speed_dataframe)
    assert result.iloc[2]["Speed"] == pytest.approx(20.0)


# --- clean_weight ---


@pytest.fixture
def weight_dataframe():
    return pd.DataFrame({"WeightInPounds": [126.0, 9.0, 0.0, 130.0, 10.0]})


def test_clean_weight_sets_invalid_to_nan(weight_dataframe):
    result = clean_weight(weight_dataframe)
    assert pd.isna(result.iloc[1]["WeightInPounds"])
    assert pd.isna(result.iloc[2]["WeightInPounds"])


def test_clean_weight_preserves_valid_weights(weight_dataframe):
    result = clean_weight(weight_dataframe)
    assert result.iloc[0]["WeightInPounds"] == 126.0
    assert result.iloc[3]["WeightInPounds"] == 130.0


def test_clean_weight_preserves_boundary_value(weight_dataframe):
    result = clean_weight(weight_dataframe)
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
    ballinrobe = result[result["RaceId"] == td.Ballinrobe20thAt1515.RaceId]
    chelmsford = result[result["RaceId"] == td.Chelmsford21stAt1805.RaceId]
    assert (ballinrobe["HorseCount"] == 3).all()
    assert (chelmsford["HorseCount"] == 2).all()


def test_calculate_horse_count_preserves_row_count(horse_count_dataframe):
    result = calculate_horse_count(horse_count_dataframe)
    assert len(result) == len(horse_count_dataframe)


# --- calculate_weight_change ---


@pytest.fixture
def weight_change_dataframe():
    return pd.DataFrame({
        "WeightInPounds": [130.0, 128.0, 126.0],
        "LastRaceWeightInPounds": [126.0, 130.0, float("nan")],
    })


def test_calculate_weight_change_adds_column(weight_change_dataframe):
    result = calculate_weight_change(weight_change_dataframe)
    assert "WeightChange" in result.columns


def test_calculate_weight_change_computes_correctly(weight_change_dataframe):
    result = calculate_weight_change(weight_change_dataframe)
    assert result.iloc[0]["WeightChange"] == pytest.approx(4.0)
    assert result.iloc[1]["WeightChange"] == pytest.approx(-2.0)


def test_calculate_weight_change_is_nan_when_last_weight_is_nan(weight_change_dataframe):
    result = calculate_weight_change(weight_change_dataframe)
    assert pd.isna(result.iloc[2]["WeightChange"])


# --- calculate_distance_change ---


@pytest.fixture
def distance_change_dataframe():
    return pd.DataFrame({
        "DistanceInMeters": [2000.0, 1600.0, 1200.0],
        "LastRaceDistanceInMeters": [1600.0, 2000.0, float("nan")],
    })


def test_calculate_distance_change_adds_column(distance_change_dataframe):
    result = calculate_distance_change(distance_change_dataframe)
    assert "DistanceChange" in result.columns


def test_calculate_distance_change_computes_correctly(distance_change_dataframe):
    result = calculate_distance_change(distance_change_dataframe)
    assert result.iloc[0]["DistanceChange"] == pytest.approx(400.0)
    assert result.iloc[1]["DistanceChange"] == pytest.approx(-400.0)


def test_calculate_distance_change_is_nan_when_last_distance_is_nan(distance_change_dataframe):
    result = calculate_distance_change(distance_change_dataframe)
    assert pd.isna(result.iloc[2]["DistanceChange"])
