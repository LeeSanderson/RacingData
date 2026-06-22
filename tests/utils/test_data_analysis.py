import pandas as pd
import pytest

import tests.utils.test_data as td
from race_analytics.features.horse_stats import CalculateHorsesStats
from race_analytics.features.jockey_stats import CalculateJockeyStats
from race_analytics.features.race_filters import CalculateRacesWithKnownHorsesAndJockeys
from race_analytics.features.trainer_stats import CalculateTrainerStats
from race_analytics.features.transforms import (
    calculateHorsesPerRace,
    encode_going,
    encode_race_type,
    encode_surfaces,
)


def test_calculateHorsesPerRace():
    data = [
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.ComeSeptember, td.SimonTorrens),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SelfAssessed, td.KevinSexton),
        td.RaceResult.new(
            td.Wolverhampton24thAt1300, td.DuckAndVanish, td.PhilipDonovan
        ),
        td.RaceResult.new(
            td.Wolverhampton24thAt1300, td.LaylaDaffodil, td.ShaneFitzgerald
        ),
    ]

    df = pd.DataFrame(data)
    result = calculateHorsesPerRace(df)
    expected_counts = [3, 3, 3, 2, 2]
    assert result["HorseCount"].tolist() == expected_counts


def test_first_day_races_are_never_known():
    """All races on the first day have no history, so KnownHorseAndJockey must be False."""
    data = [
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.ComeSeptember, td.SimonTorrens),
    ]
    df = pd.DataFrame(data)
    CalculateRacesWithKnownHorsesAndJockeys().process_race_data(df)
    assert df["KnownHorseAndJockey"].tolist() == [False, False]


def test_race_with_all_known_horses_and_jockeys_is_marked_known():
    """A race where every horse and jockey appeared in a prior race is marked True."""
    data = [
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.ComeSeptember, td.SimonTorrens),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.SimonTorrens),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.ComeSeptember, td.PaulTown),
    ]
    df = pd.DataFrame(data)
    CalculateRacesWithKnownHorsesAndJockeys().process_race_data(df)
    assert df["KnownHorseAndJockey"].iloc[2]
    assert df["KnownHorseAndJockey"].iloc[3]


def test_race_with_unknown_horse_is_not_marked_known():
    """Even if all jockeys are known, one unknown horse makes the whole race False."""
    data = [
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.LaylaDaffodil, td.PaulTown),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.SimonTorrens),
    ]
    df = pd.DataFrame(data)
    CalculateRacesWithKnownHorsesAndJockeys().process_race_data(df)
    assert not df["KnownHorseAndJockey"].iloc[1]
    assert not df["KnownHorseAndJockey"].iloc[2]


def test_race_with_unknown_jockey_is_not_marked_known():
    """Even if all horses are known, one unknown jockey makes the whole race False."""
    data = [
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.ComeSeptember, td.SimonTorrens),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.ShaneFitzgerald),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.ComeSeptember, td.PaulTown),
    ]
    df = pd.DataFrame(data)
    CalculateRacesWithKnownHorsesAndJockeys().process_race_data(df)
    assert not df["KnownHorseAndJockey"].iloc[2]
    assert not df["KnownHorseAndJockey"].iloc[3]


def test_no_races_on_intermediate_day_does_not_raise():
    """Base class skips update() on gap days (no races), so subclasses never receive an empty slice."""
    data = [
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.ComeSeptember, td.SimonTorrens),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.ComeSeptember, td.SimonTorrens),
    ]
    df = pd.DataFrame(data)
    # Should not raise KeyError
    CalculateRacesWithKnownHorsesAndJockeys().process_race_data(df)
    assert df["KnownHorseAndJockey"].iloc[2]
    assert df["KnownHorseAndJockey"].iloc[3]


def test_known_across_three_days():
    """Integration test: unknown on day 1 and 2, fully known by day 3."""
    data = [
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.ComeSeptember, td.SimonTorrens),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.DuckAndVanish, td.PhilipDonovan),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.ComeSeptember, td.PaulTown),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SelfAssessed, td.KevinSexton),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.SecretSecret, td.PhilipDonovan),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.ComeSeptember, td.KevinSexton),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.SelfAssessed, td.SimonTorrens),
    ]

    df = pd.DataFrame(data)
    CalculateRacesWithKnownHorsesAndJockeys().process_race_data(df)
    expected_known = [False, False, False, False, False, True, True, True]
    assert df["KnownHorseAndJockey"].tolist() == expected_known


@pytest.fixture
def horse_stats_dataframe() -> pd.DataFrame:
    """Two-day dataset. Day 1 = Ballinrobe (July 20), Day 2 = Chelmsford (July 21)."""
    data = [
        td.RaceResult.new(
            td.Ballinrobe20thAt1515,
            td.SecretSecret,
            td.PaulTown,
            Going="Soft",
            FinishingPosition=2,
            DistanceInMeters=2400.0,
            Speed=13.5,
            WeightInPounds=128.0,
            DecimalOdds=5.0,
            OfficialRating=85.0,
            RacingPostRating=95.0,
            TopSpeedRating=88.0,
        ),
        td.RaceResult.new(
            td.Ballinrobe20thAt1515,
            td.DuckAndVanish,
            td.PhilipDonovan,
            Going="Soft",
            FinishingPosition=1,
        ),
        td.RaceResult.new(
            td.Chelmsford21stAt1805,
            td.SecretSecret,
            td.PaulTown,
            Going="Good",
            FinishingPosition=1,
        ),
    ]
    df = pd.DataFrame(data)
    df = calculateHorsesPerRace(df)
    df = encode_surfaces(df)
    df = encode_going(df)
    df = encode_race_type(df)
    return df


def test_horse_stats_number_of_prior_races(horse_stats_dataframe: pd.DataFrame) -> None:
    CalculateHorsesStats().process_race_data(horse_stats_dataframe)
    secret_day2 = horse_stats_dataframe[
        (horse_stats_dataframe["HorseId"] == td.SecretSecret.HorseId)
        & (horse_stats_dataframe["RaceId"] == td.Chelmsford21stAt1805.RaceId)
    ].iloc[0]
    assert secret_day2["NumberOfPriorRaces"] == 1


def test_horse_stats_days_rested(horse_stats_dataframe: pd.DataFrame) -> None:
    CalculateHorsesStats().process_race_data(horse_stats_dataframe)
    secret_day2 = horse_stats_dataframe[
        (horse_stats_dataframe["HorseId"] == td.SecretSecret.HorseId)
        & (horse_stats_dataframe["RaceId"] == td.Chelmsford21stAt1805.RaceId)
    ].iloc[0]
    assert secret_day2["DaysRested"] == 1


def test_horse_stats_last_race_going_and_surface(
    horse_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateHorsesStats().process_race_data(horse_stats_dataframe)
    secret_day2 = horse_stats_dataframe[
        (horse_stats_dataframe["HorseId"] == td.SecretSecret.HorseId)
        & (horse_stats_dataframe["RaceId"] == td.Chelmsford21stAt1805.RaceId)
    ].iloc[0]
    assert secret_day2["LastRaceGoing"] == "Soft"
    assert secret_day2["LastRaceSurface"] == "Turf"


def test_horse_stats_last_race_numeric_fields(
    horse_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateHorsesStats().process_race_data(horse_stats_dataframe)
    secret_day2 = horse_stats_dataframe[
        (horse_stats_dataframe["HorseId"] == td.SecretSecret.HorseId)
        & (horse_stats_dataframe["RaceId"] == td.Chelmsford21stAt1805.RaceId)
    ].iloc[0]
    assert secret_day2["LastRaceDistanceInMeters"] == 2400.0
    assert secret_day2["LastRaceSpeed"] == pytest.approx(13.5)
    assert secret_day2["LastRaceWeightInPounds"] == 128.0
    assert secret_day2["LastRaceDecimalOdds"] == 5.0
    assert secret_day2["LastRaceOfficialRating"] == 85.0
    assert secret_day2["LastRaceRacingPostRating"] == 95.0
    assert secret_day2["LastRaceTopSpeedRating"] == 88.0


def test_horse_stats_avg_relative_finishing_position(
    horse_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateHorsesStats().process_race_data(horse_stats_dataframe)
    secret_day2 = horse_stats_dataframe[
        (horse_stats_dataframe["HorseId"] == td.SecretSecret.HorseId)
        & (horse_stats_dataframe["RaceId"] == td.Chelmsford21stAt1805.RaceId)
    ].iloc[0]
    assert secret_day2["LastRaceAvgRelFinishingPosition"] == pytest.approx(1.0)


def test_horse_stats_encoded_going_columns(
    horse_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateHorsesStats().process_race_data(horse_stats_dataframe)
    secret_day2 = horse_stats_dataframe[
        (horse_stats_dataframe["HorseId"] == td.SecretSecret.HorseId)
        & (horse_stats_dataframe["RaceId"] == td.Chelmsford21stAt1805.RaceId)
    ].iloc[0]
    assert secret_day2["LastRaceGoing_Soft"] == 1.0
    assert secret_day2["LastRaceGoing_Good"] == 0.0


def test_horse_stats_encoded_surface_columns(
    horse_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateHorsesStats().process_race_data(horse_stats_dataframe)
    secret_day2 = horse_stats_dataframe[
        (horse_stats_dataframe["HorseId"] == td.SecretSecret.HorseId)
        & (horse_stats_dataframe["RaceId"] == td.Chelmsford21stAt1805.RaceId)
    ].iloc[0]
    assert secret_day2["LastRaceSurface_Turf"] == 1.0
    assert secret_day2["LastRaceSurface_AllWeather"] == 0.0


def test_horse_stats_encoded_race_type_columns(
    horse_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateHorsesStats().process_race_data(horse_stats_dataframe)
    secret_day2 = horse_stats_dataframe[
        (horse_stats_dataframe["HorseId"] == td.SecretSecret.HorseId)
        & (horse_stats_dataframe["RaceId"] == td.Chelmsford21stAt1805.RaceId)
    ].iloc[0]
    assert secret_day2["LastRaceRaceType_Hurdle"] == 1.0
    assert secret_day2["LastRaceRaceType_Flat"] == 0.0


def test_horse_with_no_prior_history_has_nan_stats(
    horse_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateHorsesStats().process_race_data(horse_stats_dataframe)
    duck_day1 = horse_stats_dataframe[
        (horse_stats_dataframe["HorseId"] == td.DuckAndVanish.HorseId)
        & (horse_stats_dataframe["RaceId"] == td.Ballinrobe20thAt1515.RaceId)
    ].iloc[0]
    assert pd.isna(duck_day1["LastRaceGoing"])
    assert pd.isna(duck_day1["DaysRested"])


def test_horse_stats_no_error_when_new_horse_races_alongside_known_horse():
    """A daily slice with one known horse and one brand-new horse must not raise TypeError.

    Before the fix, NumberOfPriorRaces was initialised as int64 (= 1). The
    left-join merge in update() produces NaN for the new horse, and assigning
    NaN into an int64 column raises:
        TypeError: Invalid value '...' for dtype 'int64'
    The fix is to initialise the column as float (1.0) so NaN is accepted.
    """
    data = [
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.ComeSeptember, td.SimonTorrens),
    ]
    df = pd.DataFrame(data)
    df = calculateHorsesPerRace(df)
    df = encode_surfaces(df)
    df = encode_going(df)
    df = encode_race_type(df)
    CalculateHorsesStats().process_race_data(df)
    come_day2 = df[
        (df["HorseId"] == td.ComeSeptember.HorseId)
        & (df["RaceId"] == td.Chelmsford21stAt1805.RaceId)
    ].iloc[0]
    assert pd.isna(come_day2["NumberOfPriorRaces"])


@pytest.fixture
def jockey_stats_dataframe() -> pd.DataFrame:
    """
    Three-day dataset for PaulTown:
      Day 1 (Ballinrobe July 20):  2nd of 2  → no history yet
      Day 2 (Chelmsford July 21):  1st of 2  → history: day 1
      Day 3 (Nottingham July 22):  any pos   → history: day 1 + day 2
    """
    data = [
        td.RaceResult.new(
            td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown, FinishingPosition=2
        ),
        td.RaceResult.new(
            td.Ballinrobe20thAt1515,
            td.DuckAndVanish,
            td.PhilipDonovan,
            FinishingPosition=1,
        ),
        td.RaceResult.new(
            td.Chelmsford21stAt1805, td.ComeSeptember, td.PaulTown, FinishingPosition=1
        ),
        td.RaceResult.new(
            td.Chelmsford21stAt1805,
            td.LaylaDaffodil,
            td.ShaneFitzgerald,
            FinishingPosition=2,
        ),
        td.RaceResult.new(
            td.Nottingham22ndAt1815, td.SelfAssessed, td.PaulTown, FinishingPosition=1
        ),
        td.RaceResult.new(
            td.Nottingham22ndAt1815,
            td.SecretSecret,
            td.SimonTorrens,
            FinishingPosition=2,
        ),
        td.RaceResult.new(
            td.Nottingham22ndAt1815,
            td.DuckAndVanish,
            td.KevinSexton,
            FinishingPosition=3,
        ),
    ]
    df = pd.DataFrame(data)
    df = calculateHorsesPerRace(df)
    return df


def _paul_town_on(df: pd.DataFrame, race: td.Race) -> pd.Series:
    return df[
        (df["JockeyId"] == td.PaulTown.JockeyId) & (df["RaceId"] == race.RaceId)
    ].iloc[0]


def test_jockey_stats_number_of_prior_races_after_one_race(
    jockey_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateJockeyStats().process_race_data(jockey_stats_dataframe)
    row = _paul_town_on(jockey_stats_dataframe, td.Chelmsford21stAt1805)
    assert row["JockeyNumberOfPriorRaces"] == 1


def test_jockey_stats_number_of_prior_races_after_two_races(
    jockey_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateJockeyStats().process_race_data(jockey_stats_dataframe)
    row = _paul_town_on(jockey_stats_dataframe, td.Nottingham22ndAt1815)
    assert row["JockeyNumberOfPriorRaces"] == 2


def test_jockey_stats_days_since_last_race(
    jockey_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateJockeyStats().process_race_data(jockey_stats_dataframe)
    row = _paul_town_on(jockey_stats_dataframe, td.Chelmsford21stAt1805)
    assert row["DaysSinceJockeyLastRaced"] == 1


def test_jockey_stats_win_percentage_no_wins(
    jockey_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateJockeyStats().process_race_data(jockey_stats_dataframe)
    row = _paul_town_on(jockey_stats_dataframe, td.Chelmsford21stAt1805)
    assert row["JockeyWinPercentage"] == pytest.approx(0.0)


def test_jockey_stats_win_percentage_with_wins(
    jockey_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateJockeyStats().process_race_data(jockey_stats_dataframe)
    row = _paul_town_on(jockey_stats_dataframe, td.Nottingham22ndAt1815)
    assert row["JockeyWinPercentage"] == pytest.approx(0.5)


def test_jockey_stats_top3_percentage(jockey_stats_dataframe: pd.DataFrame) -> None:
    CalculateJockeyStats().process_race_data(jockey_stats_dataframe)
    row = _paul_town_on(jockey_stats_dataframe, td.Nottingham22ndAt1815)
    assert row["JockeyTop3Percentage"] == pytest.approx(1.0)


def test_jockey_stats_avg_relative_finishing_position(
    jockey_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateJockeyStats().process_race_data(jockey_stats_dataframe)
    row = _paul_town_on(jockey_stats_dataframe, td.Nottingham22ndAt1815)
    assert row["JockeyAvgRelFinishingPosition"] == pytest.approx(0.75)


def test_jockey_with_no_prior_history_keeps_default_prior_races(
    jockey_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateJockeyStats().process_race_data(jockey_stats_dataframe)
    row = _paul_town_on(jockey_stats_dataframe, td.Ballinrobe20thAt1515)
    assert row["JockeyNumberOfPriorRaces"] == pytest.approx(1.0)


@pytest.fixture
def multi_race_horse_stats_dataframe() -> pd.DataFrame:
    """
    Four-day dataset so SecretSecret has 3 prior races by day 4.
      Day 1 (Ballinrobe  July 20): SecretSecret 2nd of 2, Speed=13.0
      Day 2 (Chelmsford  July 21): SecretSecret 1st of 2, Speed=14.0
      Day 3 (Nottingham  July 22): SecretSecret 1st of 3, Speed=15.0
      Day 4 (Wolverhampton July 24): SecretSecret runs — predictions based on days 1-3
    """
    data = [
        td.RaceResult.new(
            td.Ballinrobe20thAt1515,
            td.SecretSecret,
            td.PaulTown,
            FinishingPosition=2,
            Speed=13.0,
        ),
        td.RaceResult.new(
            td.Ballinrobe20thAt1515,
            td.DuckAndVanish,
            td.PhilipDonovan,
            FinishingPosition=1,
            Speed=13.5,
        ),
        td.RaceResult.new(
            td.Chelmsford21stAt1805,
            td.SecretSecret,
            td.PaulTown,
            FinishingPosition=1,
            Speed=14.0,
        ),
        td.RaceResult.new(
            td.Chelmsford21stAt1805,
            td.DuckAndVanish,
            td.PhilipDonovan,
            FinishingPosition=2,
            Speed=13.8,
        ),
        td.RaceResult.new(
            td.Nottingham22ndAt1815,
            td.SecretSecret,
            td.PaulTown,
            FinishingPosition=1,
            Speed=15.0,
        ),
        td.RaceResult.new(
            td.Nottingham22ndAt1815,
            td.DuckAndVanish,
            td.PhilipDonovan,
            FinishingPosition=2,
            Speed=14.5,
        ),
        td.RaceResult.new(
            td.Nottingham22ndAt1815,
            td.ComeSeptember,
            td.SimonTorrens,
            FinishingPosition=3,
            Speed=14.0,
        ),
        td.RaceResult.new(
            td.Wolverhampton24thAt1300,
            td.SecretSecret,
            td.PaulTown,
            FinishingPosition=1,
            Speed=15.5,
        ),
        td.RaceResult.new(
            td.Wolverhampton24thAt1300,
            td.DuckAndVanish,
            td.PhilipDonovan,
            FinishingPosition=2,
            Speed=15.0,
        ),
    ]
    df = pd.DataFrame(data)
    df = calculateHorsesPerRace(df)
    df = encode_surfaces(df)
    df = encode_going(df)
    df = encode_race_type(df)
    return df


def _secret_on(df: pd.DataFrame, race: td.Race) -> pd.Series:
    return df[
        (df["HorseId"] == td.SecretSecret.HorseId) & (df["RaceId"] == race.RaceId)
    ].iloc[0]


def test_horse_stats_last3_avg_speed_with_3_prior_races(
    multi_race_horse_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateHorsesStats().process_race_data(multi_race_horse_stats_dataframe)
    row = _secret_on(multi_race_horse_stats_dataframe, td.Wolverhampton24thAt1300)
    assert row["Last3RaceAvgSpeed"] == pytest.approx(14.0)


def test_horse_stats_last3_speed_trend_positive_for_improving_form(
    multi_race_horse_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateHorsesStats().process_race_data(multi_race_horse_stats_dataframe)
    row = _secret_on(multi_race_horse_stats_dataframe, td.Wolverhampton24thAt1300)
    assert row["Last3RaceSpeedTrend"] == pytest.approx(1.0)


def test_horse_stats_last3_avg_rel_pos_with_3_prior_races(
    multi_race_horse_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateHorsesStats().process_race_data(multi_race_horse_stats_dataframe)
    row = _secret_on(multi_race_horse_stats_dataframe, td.Wolverhampton24thAt1300)
    assert row["Last3AvgRelFinishingPosition"] == pytest.approx(
        (1 / 3 + 1 / 2 + 2 / 2) / 3, rel=1e-4
    )


def test_horse_stats_last3_features_are_nan_with_fewer_than_3_races(
    multi_race_horse_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateHorsesStats().process_race_data(multi_race_horse_stats_dataframe)
    row = _secret_on(multi_race_horse_stats_dataframe, td.Chelmsford21stAt1805)
    # pd.isna on a scalar Series element is typed as Series | NDArray by the stubs
    assert pd.isna(row["Last3RaceAvgSpeed"])  # pyright: ignore[reportGeneralTypeIssues]
    assert pd.isna(row["Last3RaceSpeedTrend"])  # pyright: ignore[reportGeneralTypeIssues]
    assert pd.isna(row["Last3AvgRelFinishingPosition"])  # pyright: ignore[reportGeneralTypeIssues]


@pytest.fixture
def trainer_stats_dataframe() -> pd.DataFrame:
    """
    Three-day dataset for TrainerSmith:
      Day 1 (Ballinrobe July 20):  2nd of 2  → no history yet
      Day 2 (Chelmsford July 21):  1st of 2  → history: day 1
      Day 3 (Nottingham July 22):  1st of 3  → history: day 1 + day 2
    """
    data = [
        td.RaceResult.new(
            td.Ballinrobe20thAt1515,
            td.SecretSecret,
            td.PaulTown,
            FinishingPosition=2,
            trainer=td.TrainerSmith,
        ),
        td.RaceResult.new(
            td.Ballinrobe20thAt1515,
            td.DuckAndVanish,
            td.PhilipDonovan,
            FinishingPosition=1,
            trainer=td.TrainerJones,
        ),
        td.RaceResult.new(
            td.Chelmsford21stAt1805,
            td.ComeSeptember,
            td.PaulTown,
            FinishingPosition=1,
            trainer=td.TrainerSmith,
        ),
        td.RaceResult.new(
            td.Chelmsford21stAt1805,
            td.LaylaDaffodil,
            td.ShaneFitzgerald,
            FinishingPosition=2,
            trainer=td.TrainerJones,
        ),
        td.RaceResult.new(
            td.Nottingham22ndAt1815,
            td.SelfAssessed,
            td.PaulTown,
            FinishingPosition=1,
            trainer=td.TrainerSmith,
        ),
        td.RaceResult.new(
            td.Nottingham22ndAt1815,
            td.SecretSecret,
            td.SimonTorrens,
            FinishingPosition=2,
            trainer=td.TrainerJones,
        ),
        td.RaceResult.new(
            td.Nottingham22ndAt1815,
            td.DuckAndVanish,
            td.KevinSexton,
            FinishingPosition=3,
            trainer=td.TrainerJones,
        ),
    ]
    df = pd.DataFrame(data)
    df = calculateHorsesPerRace(df)
    return df


def _trainer_smith_on(df: pd.DataFrame, race: td.Race) -> pd.Series:
    return df[
        (df["TrainerId"] == td.TrainerSmith.TrainerId) & (df["RaceId"] == race.RaceId)
    ].iloc[0]


def test_trainer_stats_number_of_prior_races_after_one_race(
    trainer_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateTrainerStats().process_race_data(trainer_stats_dataframe)
    row = _trainer_smith_on(trainer_stats_dataframe, td.Chelmsford21stAt1805)
    assert row["TrainerNumberOfPriorRaces"] == 1


def test_trainer_stats_number_of_prior_races_after_two_races(
    trainer_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateTrainerStats().process_race_data(trainer_stats_dataframe)
    row = _trainer_smith_on(trainer_stats_dataframe, td.Nottingham22ndAt1815)
    assert row["TrainerNumberOfPriorRaces"] == 2


def test_trainer_stats_win_percentage_no_wins(
    trainer_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateTrainerStats().process_race_data(trainer_stats_dataframe)
    row = _trainer_smith_on(trainer_stats_dataframe, td.Chelmsford21stAt1805)
    assert row["TrainerWinPercentage"] == pytest.approx(0.0)


def test_trainer_stats_win_percentage_with_wins(
    trainer_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateTrainerStats().process_race_data(trainer_stats_dataframe)
    row = _trainer_smith_on(trainer_stats_dataframe, td.Nottingham22ndAt1815)
    assert row["TrainerWinPercentage"] == pytest.approx(0.5)


def test_trainer_stats_top3_percentage(trainer_stats_dataframe: pd.DataFrame) -> None:
    CalculateTrainerStats().process_race_data(trainer_stats_dataframe)
    row = _trainer_smith_on(trainer_stats_dataframe, td.Nottingham22ndAt1815)
    assert row["TrainerTop3Percentage"] == pytest.approx(1.0)


def test_trainer_stats_avg_relative_finishing_position(
    trainer_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateTrainerStats().process_race_data(trainer_stats_dataframe)
    row = _trainer_smith_on(trainer_stats_dataframe, td.Nottingham22ndAt1815)
    assert row["TrainerAvgRelFinishingPosition"] == pytest.approx(0.75)


def test_trainer_with_no_prior_history_keeps_default_prior_races(
    trainer_stats_dataframe: pd.DataFrame,
) -> None:
    CalculateTrainerStats().process_race_data(trainer_stats_dataframe)
    row = _trainer_smith_on(trainer_stats_dataframe, td.Ballinrobe20thAt1515)
    assert row["TrainerNumberOfPriorRaces"] == pytest.approx(1.0)
