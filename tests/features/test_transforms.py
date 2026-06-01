import pytest
import pandas as pd
import numpy as np
import tests.utils.test_data as td

from race_analytics.features.transforms import (
    surface_categories,
    going_categories,
    race_type_categories,
    pattern_categories,
    age_band_categories,
    sex_restriction_categories,
    encode_surfaces,
    encode_going,
    encode_race_type,
    calculate_speed,
    clean_weight,
    calculate_horse_count,
    calculate_weight_change,
    calculate_distance_change,
    calculate_surface_switch,
    calculate_code_switch,
    calculate_race_class,
    calculate_age_features,
    calculate_draw_features,
    encode_pattern,
    calculate_is_handicap,
    encode_age_band,
    encode_sex_restriction,
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


# --- calculate_surface_switch ---


@pytest.fixture
def surface_switch_dataframe():
    # Row 0: Turf → Turf (same surface)
    # Row 1: Turf → AllWeather (surface switch)
    # Row 2: AllWeather → AllWeather (same surface)
    # Row 3: no prior race (all LastRaceSurface_* are NaN)
    return pd.DataFrame({
        "Surface_AllWeather": [0.0, 0.0, 1.0, 0.0],
        "Surface_Dirt":       [0.0, 0.0, 0.0, 0.0],
        "Surface_Turf":       [1.0, 1.0, 0.0, 1.0],
        "LastRaceSurface_AllWeather": [0.0, 1.0, 1.0, float("nan")],
        "LastRaceSurface_Dirt":       [0.0, 0.0, 0.0, float("nan")],
        "LastRaceSurface_Turf":       [1.0, 0.0, 0.0, float("nan")],
    })


def test_calculate_surface_switch_adds_column(surface_switch_dataframe):
    result = calculate_surface_switch(surface_switch_dataframe)
    assert "SurfaceSwitch" in result.columns


def test_calculate_surface_switch_same_surface_gives_zero(surface_switch_dataframe):
    result = calculate_surface_switch(surface_switch_dataframe)
    assert result.iloc[0]["SurfaceSwitch"] == pytest.approx(0.0)
    assert result.iloc[2]["SurfaceSwitch"] == pytest.approx(0.0)


def test_calculate_surface_switch_different_surface_gives_one(surface_switch_dataframe):
    result = calculate_surface_switch(surface_switch_dataframe)
    assert result.iloc[1]["SurfaceSwitch"] == pytest.approx(1.0)


def test_calculate_surface_switch_is_nan_when_no_prior_race(surface_switch_dataframe):
    result = calculate_surface_switch(surface_switch_dataframe)
    assert pd.isna(result.iloc[3]["SurfaceSwitch"])


# --- calculate_code_switch ---


@pytest.fixture
def code_switch_dataframe():
    # Row 0: Flat → Flat (same code)
    # Row 1: Flat → Hurdle (code switch: flat to jumps)
    # Row 2: Hurdle → Flat (code switch: jumps to flat)
    # Row 3: Hurdle → SteepleChase (both jumps, same code)
    # Row 4: no prior race (all LastRaceRaceType_* are NaN)
    return pd.DataFrame({
        "RaceType_Flat":         [1.0, 1.0, 0.0, 0.0, 1.0],
        "RaceType_Hurdle":       [0.0, 0.0, 1.0, 1.0, 0.0],
        "RaceType_SteepleChase": [0.0, 0.0, 0.0, 0.0, 0.0],
        "RaceType_Other":        [0.0, 0.0, 0.0, 0.0, 0.0],
        "LastRaceRaceType_Flat":         [1.0, 0.0, 1.0, 0.0, float("nan")],
        "LastRaceRaceType_Hurdle":       [0.0, 1.0, 0.0, 0.0, float("nan")],
        "LastRaceRaceType_SteepleChase": [0.0, 0.0, 0.0, 1.0, float("nan")],
        "LastRaceRaceType_Other":        [0.0, 0.0, 0.0, 0.0, float("nan")],
    })


def test_calculate_code_switch_adds_column(code_switch_dataframe):
    result = calculate_code_switch(code_switch_dataframe)
    assert "CodeSwitch" in result.columns


def test_calculate_code_switch_flat_to_flat_is_zero(code_switch_dataframe):
    result = calculate_code_switch(code_switch_dataframe)
    assert result.iloc[0]["CodeSwitch"] == pytest.approx(0.0)


def test_calculate_code_switch_flat_to_jumps_is_one(code_switch_dataframe):
    result = calculate_code_switch(code_switch_dataframe)
    assert result.iloc[1]["CodeSwitch"] == pytest.approx(1.0)


def test_calculate_code_switch_jumps_to_flat_is_one(code_switch_dataframe):
    result = calculate_code_switch(code_switch_dataframe)
    assert result.iloc[2]["CodeSwitch"] == pytest.approx(1.0)


def test_calculate_code_switch_jumps_to_jumps_is_zero(code_switch_dataframe):
    result = calculate_code_switch(code_switch_dataframe)
    assert result.iloc[3]["CodeSwitch"] == pytest.approx(0.0)


def test_calculate_code_switch_is_nan_when_no_prior_race(code_switch_dataframe):
    result = calculate_code_switch(code_switch_dataframe)
    assert pd.isna(result.iloc[4]["CodeSwitch"])


# --- calculate_race_class ---


def test_calculate_race_class_numeric_class_is_encoded_as_float():
    df = pd.DataFrame({"Class": ["3"]})
    result = calculate_race_class(df)
    assert result.iloc[0]["RaceClass"] == pytest.approx(3.0)


def test_calculate_race_class_blank_class_gives_zero():
    df = pd.DataFrame({"Class": ["", None]})
    result = calculate_race_class(df)
    assert result.iloc[0]["RaceClass"] == pytest.approx(0.0)
    assert result.iloc[1]["RaceClass"] == pytest.approx(0.0)


def test_calculate_race_class_non_numeric_gives_zero():
    df = pd.DataFrame({"Class": ["Listed", "Novice"]})
    result = calculate_race_class(df)
    assert result.iloc[0]["RaceClass"] == pytest.approx(0.0)
    assert result.iloc[1]["RaceClass"] == pytest.approx(0.0)


def test_calculate_race_class_out_of_range_gives_zero():
    df = pd.DataFrame({"Class": ["0", "8"]})
    result = calculate_race_class(df)
    assert result.iloc[0]["RaceClass"] == pytest.approx(0.0)
    assert result.iloc[1]["RaceClass"] == pytest.approx(0.0)


def test_calculate_race_class_missing_column_gives_nan():
    df = pd.DataFrame({"Other": [1, 2]})
    result = calculate_race_class(df)
    assert pd.isna(result.iloc[0]["RaceClass"])


# --- calculate_age_features ---


def test_calculate_age_features_adds_relage_column():
    df = pd.DataFrame({"RaceId": [1, 1], "Age": [3, 5]})
    result = calculate_age_features(df)
    assert "RelAge" in result.columns


def test_calculate_age_features_relage_is_zero_for_uniform_field():
    df = pd.DataFrame({"RaceId": [1, 1, 1], "Age": [3, 3, 3]})
    result = calculate_age_features(df)
    assert result["RelAge"].tolist() == pytest.approx([0.0, 0.0, 0.0])


def test_calculate_age_features_relage_correct():
    df = pd.DataFrame({"RaceId": [1, 1], "Age": [3, 4]})
    result = calculate_age_features(df)
    assert result.iloc[0]["RelAge"] == pytest.approx(-0.5)
    assert result.iloc[1]["RelAge"] == pytest.approx(0.5)


def test_calculate_age_features_nan_age_propagates():
    df = pd.DataFrame({"RaceId": [1, 1], "Age": [3, float("nan")]})
    result = calculate_age_features(df)
    assert pd.isna(result.iloc[1]["RelAge"])


def test_calculate_age_features_missing_column_gives_nan():
    df = pd.DataFrame({"RaceId": [1, 2], "Other": [3, 4]})
    result = calculate_age_features(df)
    assert pd.isna(result.iloc[0]["RelAge"])


# --- calculate_draw_features ---


@pytest.fixture
def draw_dataframe():
    # Row 0: flat, stall 2 of 8 horses → DrawPct 0.25
    # Row 1: flat, stall 6 of 8 horses → DrawPct 0.75
    # Row 2: jumps race → NaN
    # Row 3: flat, null stall → NaN
    return pd.DataFrame({
        "RaceType_Flat": [1.0, 1.0, 0.0, 1.0],
        "StallNumber":   [2.0, 6.0, 3.0, float("nan")],
        "HorseCount":    [8.0, 8.0, 8.0, 8.0],
    })


def test_calculate_draw_features_flat_race_computes_draw_pct(draw_dataframe):
    result = calculate_draw_features(draw_dataframe)
    assert result.iloc[0]["DrawPct"] == pytest.approx(0.25)


def test_calculate_draw_features_reldraw_is_centered(draw_dataframe):
    result = calculate_draw_features(draw_dataframe)
    assert result.iloc[0]["RelDraw"] == pytest.approx(-0.25)
    assert result.iloc[1]["RelDraw"] == pytest.approx(0.25)


def test_calculate_draw_features_jumps_race_gives_nan(draw_dataframe):
    result = calculate_draw_features(draw_dataframe)
    assert pd.isna(result.iloc[2]["DrawPct"])
    assert pd.isna(result.iloc[2]["RelDraw"])


def test_calculate_draw_features_null_stall_gives_nan(draw_dataframe):
    result = calculate_draw_features(draw_dataframe)
    assert pd.isna(result.iloc[3]["DrawPct"])
    assert pd.isna(result.iloc[3]["RelDraw"])


def test_calculate_draw_features_missing_stall_column_gives_nan():
    df = pd.DataFrame({"RaceType_Flat": [1.0], "HorseCount": [8.0]})
    result = calculate_draw_features(df)
    assert pd.isna(result.iloc[0]["DrawPct"])
    assert pd.isna(result.iloc[0]["RelDraw"])


# --- encode_pattern ---


def test_encode_pattern_group1_is_encoded():
    df = pd.DataFrame({"Pattern": ["Group 1", "G1", "Grade 1"]})
    result = encode_pattern(df)
    assert result.iloc[0]["Pattern_Group1"] == pytest.approx(1.0)
    assert result.iloc[1]["Pattern_Group1"] == pytest.approx(1.0)
    assert result.iloc[2]["Pattern_Group1"] == pytest.approx(1.0)


def test_encode_pattern_blank_gives_none_category():
    df = pd.DataFrame({"Pattern": ["", None]})
    result = encode_pattern(df)
    assert result.iloc[0]["Pattern_None"] == pytest.approx(1.0)
    assert result.iloc[1]["Pattern_None"] == pytest.approx(1.0)


def test_encode_pattern_unknown_gives_none_category():
    df = pd.DataFrame({"Pattern": ["Bumper", "Unknown"]})
    result = encode_pattern(df)
    assert result.iloc[0]["Pattern_None"] == pytest.approx(1.0)


def test_encode_pattern_all_categories_present():
    df = pd.DataFrame({"Pattern": ["Group 1"]})
    result = encode_pattern(df)
    for col in pattern_categories:
        assert col in result.columns


def test_encode_pattern_missing_column_all_zeros():
    df = pd.DataFrame({"Other": [1, 2]})
    result = encode_pattern(df)
    for col in pattern_categories:
        assert col in result.columns
        assert result.iloc[0][col] == pytest.approx(0.0)


# --- calculate_is_handicap ---


def test_calculate_is_handicap_non_empty_gives_one():
    df = pd.DataFrame({"RatingBand": ["0-70", "71-90"]})
    result = calculate_is_handicap(df)
    assert result.iloc[0]["IsHandicap"] == pytest.approx(1.0)
    assert result.iloc[1]["IsHandicap"] == pytest.approx(1.0)


def test_calculate_is_handicap_empty_string_gives_zero():
    df = pd.DataFrame({"RatingBand": [""]})
    result = calculate_is_handicap(df)
    assert result.iloc[0]["IsHandicap"] == pytest.approx(0.0)


def test_calculate_is_handicap_nan_gives_zero():
    df = pd.DataFrame({"RatingBand": [None]})
    result = calculate_is_handicap(df)
    assert result.iloc[0]["IsHandicap"] == pytest.approx(0.0)


def test_calculate_is_handicap_missing_column_gives_nan():
    df = pd.DataFrame({"Other": [1]})
    result = calculate_is_handicap(df)
    assert pd.isna(result.iloc[0]["IsHandicap"])


# --- encode_age_band ---


def test_encode_age_band_2yo_is_encoded():
    df = pd.DataFrame({"AgeBand": ["2yo"]})
    result = encode_age_band(df)
    assert result.iloc[0]["AgeBand_2yo"] == pytest.approx(1.0)
    assert result.iloc[0]["AgeBand_None"] == pytest.approx(0.0)


def test_encode_age_band_blank_gives_none_category():
    df = pd.DataFrame({"AgeBand": ["", None]})
    result = encode_age_band(df)
    assert result.iloc[0]["AgeBand_None"] == pytest.approx(1.0)
    assert result.iloc[1]["AgeBand_None"] == pytest.approx(1.0)


def test_encode_age_band_all_categories_present():
    df = pd.DataFrame({"AgeBand": ["3yo+"]})
    result = encode_age_band(df)
    for col in age_band_categories:
        assert col in result.columns


# --- encode_sex_restriction ---


def test_encode_sex_restriction_fillies_is_encoded():
    df = pd.DataFrame({"SexRestriction": ["F", "Fillies"]})
    result = encode_sex_restriction(df)
    assert result.iloc[0]["SexRestriction_F"] == pytest.approx(1.0)
    assert result.iloc[1]["SexRestriction_F"] == pytest.approx(1.0)


def test_encode_sex_restriction_blank_gives_open_category():
    df = pd.DataFrame({"SexRestriction": ["", None]})
    result = encode_sex_restriction(df)
    assert result.iloc[0]["SexRestriction_Open"] == pytest.approx(1.0)
    assert result.iloc[1]["SexRestriction_Open"] == pytest.approx(1.0)


def test_encode_sex_restriction_all_categories_present():
    df = pd.DataFrame({"SexRestriction": ["F&M"]})
    result = encode_sex_restriction(df)
    for col in sex_restriction_categories:
        assert col in result.columns
