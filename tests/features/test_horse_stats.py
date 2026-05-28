import pytest
import pandas as pd
import numpy as np
import tests.utils.test_data as td

from race_analytics.features.horse_stats import CalculateHorsesStats, extract_horse_stats
from race_analytics.features.transforms import calculateHorsesPerRace
from race_analytics.features.transforms import encode_surfaces, encode_going, encode_race_type


def _make_processed_df(*race_results):
    df = pd.DataFrame(list(race_results))
    df = calculateHorsesPerRace(df)
    df = encode_surfaces(df)
    df = encode_going(df)
    df = encode_race_type(df)
    return df


def _secret_on(df, race):
    return df[
        (df["HorseId"] == td.SecretSecret.HorseId) & (df["RaceId"] == race.RaceId)
    ].iloc[0]


@pytest.fixture
def two_day_df():
    """Day 1 = Ballinrobe (July 20), Day 2 = Chelmsford (July 21)."""
    return _make_processed_df(
        td.RaceResult.new(
            td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown,
            Going="Soft", FinishingPosition=2, DistanceInMeters=2400.0,
            Speed=13.5, WeightInPounds=128.0, DecimalOdds=5.0,
            OfficialRating=85.0, RacingPostRating=95.0, TopSpeedRating=88.0,
        ),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.DuckAndVanish, td.PhilipDonovan, Going="Soft", FinishingPosition=1),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.PaulTown, Going="Good", FinishingPosition=1),
    )


def test_horse_with_no_prior_races_has_nan_stats(two_day_df):
    CalculateHorsesStats().process_race_data(two_day_df)
    duck_day1 = two_day_df[
        (two_day_df["HorseId"] == td.DuckAndVanish.HorseId)
        & (two_day_df["RaceId"] == td.Ballinrobe20thAt1515.RaceId)
    ].iloc[0]
    assert pd.isna(duck_day1["LastRaceGoing"])
    assert pd.isna(duck_day1["DaysRested"])
    assert pd.isna(duck_day1["LastRaceSpeed"])


def test_horse_with_one_prior_race_has_last_race_features(two_day_df):
    CalculateHorsesStats().process_race_data(two_day_df)
    row = _secret_on(two_day_df, td.Chelmsford21stAt1805)
    assert row["NumberOfPriorRaces"] == 1
    assert row["DaysRested"] == 1
    assert row["LastRaceDistanceInMeters"] == 2400.0
    assert row["LastRaceSpeed"] == pytest.approx(13.5)
    assert row["LastRaceWeightInPounds"] == 128.0
    assert row["LastRaceGoing"] == "Soft"
    assert row["LastRaceSurface"] == "Turf"


def test_horse_with_one_prior_race_has_nan_for_3race_aggregates(two_day_df):
    CalculateHorsesStats().process_race_data(two_day_df)
    row = _secret_on(two_day_df, td.Chelmsford21stAt1805)
    assert pd.isna(row["Last3RaceAvgSpeed"])
    assert pd.isna(row["Last3RaceSpeedTrend"])
    assert pd.isna(row["Last3AvgRelFinishingPosition"])


@pytest.fixture
def four_day_df():
    """SecretSecret has 3 prior races by day 4."""
    return _make_processed_df(
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown, FinishingPosition=2, Speed=13.0),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.DuckAndVanish, td.PhilipDonovan, FinishingPosition=1, Speed=13.5),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.PaulTown, FinishingPosition=1, Speed=14.0),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.DuckAndVanish, td.PhilipDonovan, FinishingPosition=2, Speed=13.8),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.SecretSecret, td.PaulTown, FinishingPosition=1, Speed=15.0),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.DuckAndVanish, td.PhilipDonovan, FinishingPosition=2, Speed=14.5),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.ComeSeptember, td.SimonTorrens, FinishingPosition=3, Speed=14.0),
        td.RaceResult.new(td.Wolverhampton24thAt1300, td.SecretSecret, td.PaulTown, FinishingPosition=1, Speed=15.5),
        td.RaceResult.new(td.Wolverhampton24thAt1300, td.DuckAndVanish, td.PhilipDonovan, FinishingPosition=2, Speed=15.0),
    )


def test_horse_with_3_prior_races_has_all_features(four_day_df):
    CalculateHorsesStats().process_race_data(four_day_df)
    row = _secret_on(four_day_df, td.Wolverhampton24thAt1300)
    # Last 3 speeds: 15.0, 14.0, 13.0 → avg = 14.0
    assert row["Last3RaceAvgSpeed"] == pytest.approx(14.0)
    # trend = lastSpeed(15.0) - avg(14.0) = 1.0
    assert row["Last3RaceSpeedTrend"] == pytest.approx(1.0)
    # rel pos: day3=1/3, day2=1/2, day1=2/2 → mean ≈ 0.611
    assert row["Last3AvgRelFinishingPosition"] == pytest.approx((1/3 + 1/2 + 1.0) / 3, rel=1e-4)


def test_extract_horse_stats_exports_last3_over_most_recent_races(four_day_df):
    CalculateHorsesStats().process_race_data(four_day_df)
    stats = extract_horse_stats(four_day_df)
    row = stats[stats["HorseId"] == td.SecretSecret.HorseId].iloc[0]
    # 3 most recent races (incl. latest): Wolverhampton 15.5, Nottingham 15.0,
    # Chelmsford 14.0 -> avg = 14.8333; trend = lastSpeed(15.5) - avg.
    expected_avg = (15.5 + 15.0 + 14.0) / 3
    assert "Last3RaceAvgSpeed" in stats.columns
    assert row["Last3RaceAvgSpeed"] == pytest.approx(expected_avg)
    assert row["Last3RaceSpeedTrend"] == pytest.approx(15.5 - expected_avg)
    # rel pos: Wolverhampton 1/2, Nottingham 1/3, Chelmsford 1/2.
    assert row["Last3AvgRelFinishingPosition"] == pytest.approx((0.5 + 1 / 3 + 0.5) / 3)


def test_extract_horse_stats_last3_nan_with_fewer_than_3_races(two_day_df):
    CalculateHorsesStats().process_race_data(two_day_df)
    stats = extract_horse_stats(two_day_df)
    row = stats[stats["HorseId"] == td.SecretSecret.HorseId].iloc[0]
    assert pd.isna(row["Last3RaceAvgSpeed"])
    assert pd.isna(row["Last3RaceSpeedTrend"])
    assert pd.isna(row["Last3AvgRelFinishingPosition"])


def test_incremental_processing_updates_stats_across_days(four_day_df):
    CalculateHorsesStats().process_race_data(four_day_df)
    row_day2 = _secret_on(four_day_df, td.Chelmsford21stAt1805)
    row_day4 = _secret_on(four_day_df, td.Wolverhampton24thAt1300)
    assert row_day2["NumberOfPriorRaces"] == 1
    assert row_day4["NumberOfPriorRaces"] == 3


def test_horse_stats_encoded_going_columns(two_day_df):
    CalculateHorsesStats().process_race_data(two_day_df)
    row = _secret_on(two_day_df, td.Chelmsford21stAt1805)
    assert row["LastRaceGoing_Soft"] == 1.0
    assert row["LastRaceGoing_Good"] == 0.0


def test_horse_stats_encoded_surface_columns(two_day_df):
    CalculateHorsesStats().process_race_data(two_day_df)
    row = _secret_on(two_day_df, td.Chelmsford21stAt1805)
    assert row["LastRaceSurface_Turf"] == 1.0
    assert row["LastRaceSurface_AllWeather"] == 0.0
