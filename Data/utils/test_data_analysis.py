import pytest
import pandas as pd
import utils.test_data as td

from utils.data_analysis import (
    calculateHorsesPerRace,
    CalculateRacesWithKnownHorsesAndJockeys,
    CalculateHorsesStats,
    CalculateJockeyStats,
)
from utils.data_transforms import encode_surfaces, encode_going, encode_race_type


# ================================================================
# calculateHorsesPerRace
# ================================================================

def test_calculateHorsesPerRace():
    data = [
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.ComeSeptember, td.SimonTorrens),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SelfAssessed, td.KevinSexton),

        td.RaceResult.new(td.Wolverhampton24thAt1300, td.DuckAndVanish, td.PhilipDonovan),
        td.RaceResult.new(td.Wolverhampton24thAt1300, td.LaylaDaffodil, td.ShaneFitzgerald),
    ]

    df = pd.DataFrame(data)
    result = calculateHorsesPerRace(df)
    expected_counts = [3, 3, 3, 2, 2]
    assert result["HorseCount"].tolist() == expected_counts


# ================================================================
# CalculateRacesWithKnownHorsesAndJockeys
# ================================================================

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
        # Day 1: establish history for SecretSecret/PaulTown and ComeSeptember/SimonTorrens
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.ComeSeptember, td.SimonTorrens),
        # Day 2: same horses and jockeys → all known
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.SimonTorrens),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.ComeSeptember, td.PaulTown),
    ]
    df = pd.DataFrame(data)
    CalculateRacesWithKnownHorsesAndJockeys().process_race_data(df)
    assert df["KnownHorseAndJockey"].iloc[2] == True
    assert df["KnownHorseAndJockey"].iloc[3] == True


def test_race_with_unknown_horse_is_not_marked_known():
    """Even if all jockeys are known, one unknown horse makes the whole race False."""
    data = [
        # Day 1: only PaulTown and SecretSecret seen
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown),
        # Day 2: LaylaDaffodil is a new horse, so the race is unknown
        td.RaceResult.new(td.Chelmsford21stAt1805, td.LaylaDaffodil, td.PaulTown),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.SimonTorrens),
    ]
    df = pd.DataFrame(data)
    CalculateRacesWithKnownHorsesAndJockeys().process_race_data(df)
    assert df["KnownHorseAndJockey"].iloc[1] == False
    assert df["KnownHorseAndJockey"].iloc[2] == False


def test_race_with_unknown_jockey_is_not_marked_known():
    """Even if all horses are known, one unknown jockey makes the whole race False."""
    data = [
        # Day 1: only SecretSecret and ComeSeptember seen, with PaulTown and SimonTorrens
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.ComeSeptember, td.SimonTorrens),
        # Day 2: ShaneFitzgerald is a new jockey
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.ShaneFitzgerald),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.ComeSeptember, td.PaulTown),
    ]
    df = pd.DataFrame(data)
    CalculateRacesWithKnownHorsesAndJockeys().process_race_data(df)
    assert df["KnownHorseAndJockey"].iloc[2] == False
    assert df["KnownHorseAndJockey"].iloc[3] == False


def test_no_races_on_intermediate_day_does_not_raise():
    """Base class skips update() on gap days (no races), so subclasses never receive an empty slice."""
    data = [
        # July 20: establish history
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.ComeSeptember, td.SimonTorrens),
        # July 21: no races (gap day) — iterator visits it with empty daily_slice
        # July 22: same horses and jockeys → all known
        td.RaceResult.new(td.Nottingham22ndAt1815, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.ComeSeptember, td.SimonTorrens),
    ]
    df = pd.DataFrame(data)
    # Should not raise KeyError
    CalculateRacesWithKnownHorsesAndJockeys().process_race_data(df)
    assert df["KnownHorseAndJockey"].iloc[2] == True
    assert df["KnownHorseAndJockey"].iloc[3] == True


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


# ================================================================
# CalculateHorsesStats
# ================================================================

@pytest.fixture
def horse_stats_dataframe():
    """Two-day dataset. Day 1 = Ballinrobe (July 20), Day 2 = Chelmsford (July 21)."""
    data = [
        # Day 1: two horses, SecretSecret finishes 2nd
        td.RaceResult.new(
            td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown,
            Going="Soft", FinishingPosition=2, DistanceInMeters=2400.0, Speed=13.5,
            WeightInPounds=128.0, DecimalOdds=5.0, OfficialRating=85.0,
            RacingPostRating=95.0, TopSpeedRating=88.0,
        ),
        td.RaceResult.new(
            td.Ballinrobe20thAt1515, td.DuckAndVanish, td.PhilipDonovan,
            Going="Soft", FinishingPosition=1,
        ),
        # Day 2: SecretSecret runs again
        td.RaceResult.new(
            td.Chelmsford21stAt1805, td.SecretSecret, td.PaulTown,
            Going="Good", FinishingPosition=1,
        ),
    ]
    df = pd.DataFrame(data)
    df = calculateHorsesPerRace(df)
    df = encode_surfaces(df)
    df = encode_going(df)
    df = encode_race_type(df)
    return df


def test_horse_stats_number_of_prior_races(horse_stats_dataframe):
    CalculateHorsesStats().process_race_data(horse_stats_dataframe)
    secret_day2 = horse_stats_dataframe[
        (horse_stats_dataframe["HorseId"] == td.SecretSecret.HorseId) &
        (horse_stats_dataframe["RaceId"] == td.Chelmsford21stAt1805.RaceId)
    ].iloc[0]
    assert secret_day2["NumberOfPriorRaces"] == 1


def test_horse_stats_days_rested(horse_stats_dataframe):
    CalculateHorsesStats().process_race_data(horse_stats_dataframe)
    secret_day2 = horse_stats_dataframe[
        (horse_stats_dataframe["HorseId"] == td.SecretSecret.HorseId) &
        (horse_stats_dataframe["RaceId"] == td.Chelmsford21stAt1805.RaceId)
    ].iloc[0]
    assert secret_day2["DaysRested"] == 1


def test_horse_stats_last_race_going_and_surface(horse_stats_dataframe):
    CalculateHorsesStats().process_race_data(horse_stats_dataframe)
    secret_day2 = horse_stats_dataframe[
        (horse_stats_dataframe["HorseId"] == td.SecretSecret.HorseId) &
        (horse_stats_dataframe["RaceId"] == td.Chelmsford21stAt1805.RaceId)
    ].iloc[0]
    assert secret_day2["LastRaceGoing"] == "Soft"
    assert secret_day2["LastRaceSurface"] == "Turf"


def test_horse_stats_last_race_numeric_fields(horse_stats_dataframe):
    CalculateHorsesStats().process_race_data(horse_stats_dataframe)
    secret_day2 = horse_stats_dataframe[
        (horse_stats_dataframe["HorseId"] == td.SecretSecret.HorseId) &
        (horse_stats_dataframe["RaceId"] == td.Chelmsford21stAt1805.RaceId)
    ].iloc[0]
    assert secret_day2["LastRaceDistanceInMeters"] == 2400.0
    assert secret_day2["LastRaceSpeed"] == pytest.approx(13.5)
    assert secret_day2["LastRaceWeightInPounds"] == 128.0
    assert secret_day2["LastRaceDecimalOdds"] == 5.0
    assert secret_day2["LastRaceOfficialRating"] == 85.0
    assert secret_day2["LastRaceRacingPostRating"] == 95.0
    assert secret_day2["LastRaceTopSpeedRating"] == 88.0


def test_horse_stats_avg_relative_finishing_position(horse_stats_dataframe):
    CalculateHorsesStats().process_race_data(horse_stats_dataframe)
    secret_day2 = horse_stats_dataframe[
        (horse_stats_dataframe["HorseId"] == td.SecretSecret.HorseId) &
        (horse_stats_dataframe["RaceId"] == td.Chelmsford21stAt1805.RaceId)
    ].iloc[0]
    # SecretSecret finished 2nd of 2 on day 1 → relative = 2/2 = 1.0
    assert secret_day2["LastRaceAvgRelFinishingPosition"] == pytest.approx(1.0)


def test_horse_stats_encoded_going_columns(horse_stats_dataframe):
    CalculateHorsesStats().process_race_data(horse_stats_dataframe)
    secret_day2 = horse_stats_dataframe[
        (horse_stats_dataframe["HorseId"] == td.SecretSecret.HorseId) &
        (horse_stats_dataframe["RaceId"] == td.Chelmsford21stAt1805.RaceId)
    ].iloc[0]
    assert secret_day2["LastRaceGoing_Soft"] == 1.0
    assert secret_day2["LastRaceGoing_Good"] == 0.0


def test_horse_stats_encoded_surface_columns(horse_stats_dataframe):
    CalculateHorsesStats().process_race_data(horse_stats_dataframe)
    secret_day2 = horse_stats_dataframe[
        (horse_stats_dataframe["HorseId"] == td.SecretSecret.HorseId) &
        (horse_stats_dataframe["RaceId"] == td.Chelmsford21stAt1805.RaceId)
    ].iloc[0]
    assert secret_day2["LastRaceSurface_Turf"] == 1.0
    assert secret_day2["LastRaceSurface_AllWeather"] == 0.0


def test_horse_stats_encoded_race_type_columns(horse_stats_dataframe):
    CalculateHorsesStats().process_race_data(horse_stats_dataframe)
    secret_day2 = horse_stats_dataframe[
        (horse_stats_dataframe["HorseId"] == td.SecretSecret.HorseId) &
        (horse_stats_dataframe["RaceId"] == td.Chelmsford21stAt1805.RaceId)
    ].iloc[0]
    # Ballinrobe is a Hurdle race
    assert secret_day2["LastRaceRaceType_Hurdle"] == 1.0
    assert secret_day2["LastRaceRaceType_Flat"] == 0.0


def test_horse_with_no_prior_history_has_nan_stats(horse_stats_dataframe):
    CalculateHorsesStats().process_race_data(horse_stats_dataframe)
    duck_day1 = horse_stats_dataframe[
        (horse_stats_dataframe["HorseId"] == td.DuckAndVanish.HorseId) &
        (horse_stats_dataframe["RaceId"] == td.Ballinrobe20thAt1515.RaceId)
    ].iloc[0]
    assert pd.isna(duck_day1["LastRaceGoing"])
    assert pd.isna(duck_day1["DaysRested"])


# ================================================================
# CalculateJockeyStats
# ================================================================

@pytest.fixture
def jockey_stats_dataframe():
    """
    Three-day dataset for PaulTown:
      Day 1 (Ballinrobe July 20):  2nd of 2  → no history yet
      Day 2 (Chelmsford July 21):  1st of 2  → history: day 1
      Day 3 (Nottingham July 22):  any pos   → history: day 1 + day 2
    """
    data = [
        # Day 1
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown,
                          FinishingPosition=2),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.DuckAndVanish, td.PhilipDonovan,
                          FinishingPosition=1),
        # Day 2
        td.RaceResult.new(td.Chelmsford21stAt1805, td.ComeSeptember, td.PaulTown,
                          FinishingPosition=1),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.LaylaDaffodil, td.ShaneFitzgerald,
                          FinishingPosition=2),
        # Day 3
        td.RaceResult.new(td.Nottingham22ndAt1815, td.SelfAssessed, td.PaulTown,
                          FinishingPosition=1),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.SecretSecret, td.SimonTorrens,
                          FinishingPosition=2),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.DuckAndVanish, td.KevinSexton,
                          FinishingPosition=3),
    ]
    df = pd.DataFrame(data)
    df = calculateHorsesPerRace(df)
    return df


def _paul_town_on(df, race):
    return df[
        (df["JockeyId"] == td.PaulTown.JockeyId) &
        (df["RaceId"] == race.RaceId)
    ].iloc[0]


def test_jockey_stats_number_of_prior_races_after_one_race(jockey_stats_dataframe):
    CalculateJockeyStats().process_race_data(jockey_stats_dataframe)
    row = _paul_town_on(jockey_stats_dataframe, td.Chelmsford21stAt1805)
    assert row["JockeyNumberOfPriorRaces"] == 1


def test_jockey_stats_number_of_prior_races_after_two_races(jockey_stats_dataframe):
    CalculateJockeyStats().process_race_data(jockey_stats_dataframe)
    row = _paul_town_on(jockey_stats_dataframe, td.Nottingham22ndAt1815)
    assert row["JockeyNumberOfPriorRaces"] == 2


def test_jockey_stats_days_since_last_race(jockey_stats_dataframe):
    CalculateJockeyStats().process_race_data(jockey_stats_dataframe)
    # Day 2 history is day 1 (July 20); day 2 is July 21 → 1 day
    row = _paul_town_on(jockey_stats_dataframe, td.Chelmsford21stAt1805)
    assert row["DaysSinceJockeyLastRaced"] == 1


def test_jockey_stats_win_percentage_no_wins(jockey_stats_dataframe):
    CalculateJockeyStats().process_race_data(jockey_stats_dataframe)
    # Day 2: history = day 1 only, where PaulTown finished 2nd → 0 wins
    row = _paul_town_on(jockey_stats_dataframe, td.Chelmsford21stAt1805)
    assert row["JockeyWinPercentage"] == pytest.approx(0.0)


def test_jockey_stats_win_percentage_with_wins(jockey_stats_dataframe):
    CalculateJockeyStats().process_race_data(jockey_stats_dataframe)
    # Day 3: history = day 1 (2nd) + day 2 (1st) → 1 win of 2 races = 0.5
    row = _paul_town_on(jockey_stats_dataframe, td.Nottingham22ndAt1815)
    assert row["JockeyWinPercentage"] == pytest.approx(0.5)


def test_jockey_stats_top3_percentage(jockey_stats_dataframe):
    CalculateJockeyStats().process_race_data(jockey_stats_dataframe)
    # Day 3: day 1 = 2nd (< 4), day 2 = 1st (< 4) → 2/2 = 1.0
    row = _paul_town_on(jockey_stats_dataframe, td.Nottingham22ndAt1815)
    assert row["JockeyTop3Percentage"] == pytest.approx(1.0)


def test_jockey_stats_avg_relative_finishing_position(jockey_stats_dataframe):
    CalculateJockeyStats().process_race_data(jockey_stats_dataframe)
    # Day 3: day 1 = 2nd of 2 (1.0), day 2 = 1st of 2 (0.5) → mean = 0.75
    row = _paul_town_on(jockey_stats_dataframe, td.Nottingham22ndAt1815)
    assert row["JockeyAvgRelFinishingPosition"] == pytest.approx(0.75)


def test_jockey_with_no_prior_history_keeps_default_prior_races(jockey_stats_dataframe):
    CalculateJockeyStats().process_race_data(jockey_stats_dataframe)
    # Day 1: PaulTown has no history → JockeyNumberOfPriorRaces stays at the default 1.0
    row = _paul_town_on(jockey_stats_dataframe, td.Ballinrobe20thAt1515)
    assert row["JockeyNumberOfPriorRaces"] == pytest.approx(1.0)
