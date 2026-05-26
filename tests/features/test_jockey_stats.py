import pytest
import pandas as pd
import tests.utils.test_data as td

from race_analytics.features.jockey_stats import CalculateJockeyStats
from race_analytics.utils.data_analysis import calculateHorsesPerRace


def _paul_town_on(df, race):
    return df[
        (df["JockeyId"] == td.PaulTown.JockeyId) & (df["RaceId"] == race.RaceId)
    ].iloc[0]


@pytest.fixture
def three_day_df():
    """PaulTown: day1=2nd/2, day2=1st/2, day3=any."""
    data = [
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown, FinishingPosition=2),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.DuckAndVanish, td.PhilipDonovan, FinishingPosition=1),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.ComeSeptember, td.PaulTown, FinishingPosition=1),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.LaylaDaffodil, td.ShaneFitzgerald, FinishingPosition=2),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.SelfAssessed, td.PaulTown, FinishingPosition=1),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.SecretSecret, td.SimonTorrens, FinishingPosition=2),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.DuckAndVanish, td.KevinSexton, FinishingPosition=3),
    ]
    df = pd.DataFrame(data)
    return calculateHorsesPerRace(df)


def test_jockey_with_no_prior_races_keeps_default(three_day_df):
    CalculateJockeyStats().process_race_data(three_day_df)
    row = _paul_town_on(three_day_df, td.Ballinrobe20thAt1515)
    assert row["JockeyNumberOfPriorRaces"] == pytest.approx(1.0)


def test_days_since_jockey_last_raced(three_day_df):
    CalculateJockeyStats().process_race_data(three_day_df)
    row = _paul_town_on(three_day_df, td.Chelmsford21stAt1805)
    assert row["DaysSinceJockeyLastRaced"] == 1


def test_win_percentage_with_no_wins(three_day_df):
    CalculateJockeyStats().process_race_data(three_day_df)
    row = _paul_town_on(three_day_df, td.Chelmsford21stAt1805)
    assert row["JockeyWinPercentage"] == pytest.approx(0.0)


def test_win_percentage_with_wins(three_day_df):
    CalculateJockeyStats().process_race_data(three_day_df)
    # Day 3: history = day1 (2nd) + day2 (1st) → 1 win of 2 = 0.5
    row = _paul_town_on(three_day_df, td.Nottingham22ndAt1815)
    assert row["JockeyWinPercentage"] == pytest.approx(0.5)


def test_top3_percentage(three_day_df):
    CalculateJockeyStats().process_race_data(three_day_df)
    row = _paul_town_on(three_day_df, td.Nottingham22ndAt1815)
    assert row["JockeyTop3Percentage"] == pytest.approx(1.0)


def test_avg_relative_finishing_position(three_day_df):
    CalculateJockeyStats().process_race_data(three_day_df)
    # day1: 2nd/2=1.0, day2: 1st/2=0.5 → mean=0.75
    row = _paul_town_on(three_day_df, td.Nottingham22ndAt1815)
    assert row["JockeyAvgRelFinishingPosition"] == pytest.approx(0.75)


def test_incremental_processing_updates_prior_race_count(three_day_df):
    CalculateJockeyStats().process_race_data(three_day_df)
    row_day2 = _paul_town_on(three_day_df, td.Chelmsford21stAt1805)
    row_day3 = _paul_town_on(three_day_df, td.Nottingham22ndAt1815)
    assert row_day2["JockeyNumberOfPriorRaces"] == 1
    assert row_day3["JockeyNumberOfPriorRaces"] == 2
