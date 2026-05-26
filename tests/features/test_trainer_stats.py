import pytest
import pandas as pd
import tests.utils.test_data as td

from race_analytics.features.trainer_stats import CalculateTrainerStats
from race_analytics.features.transforms import calculateHorsesPerRace


def _smith_on(df, race):
    return df[
        (df["TrainerId"] == td.TrainerSmith.TrainerId) & (df["RaceId"] == race.RaceId)
    ].iloc[0]


@pytest.fixture
def three_day_df():
    """TrainerSmith: day1=2nd/2, day2=1st/2, day3=1st/3."""
    data = [
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown, FinishingPosition=2, trainer=td.TrainerSmith),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.DuckAndVanish, td.PhilipDonovan, FinishingPosition=1, trainer=td.TrainerJones),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.ComeSeptember, td.PaulTown, FinishingPosition=1, trainer=td.TrainerSmith),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.LaylaDaffodil, td.ShaneFitzgerald, FinishingPosition=2, trainer=td.TrainerJones),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.SelfAssessed, td.PaulTown, FinishingPosition=1, trainer=td.TrainerSmith),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.SecretSecret, td.SimonTorrens, FinishingPosition=2, trainer=td.TrainerJones),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.DuckAndVanish, td.KevinSexton, FinishingPosition=3, trainer=td.TrainerJones),
    ]
    df = pd.DataFrame(data)
    return calculateHorsesPerRace(df)


def test_trainer_with_no_prior_races_keeps_default(three_day_df):
    CalculateTrainerStats().process_race_data(three_day_df)
    row = _smith_on(three_day_df, td.Ballinrobe20thAt1515)
    assert row["TrainerNumberOfPriorRaces"] == pytest.approx(1.0)


def test_number_of_prior_races_increments(three_day_df):
    CalculateTrainerStats().process_race_data(three_day_df)
    assert _smith_on(three_day_df, td.Chelmsford21stAt1805)["TrainerNumberOfPriorRaces"] == 1
    assert _smith_on(three_day_df, td.Nottingham22ndAt1815)["TrainerNumberOfPriorRaces"] == 2


def test_win_percentage_no_wins(three_day_df):
    CalculateTrainerStats().process_race_data(three_day_df)
    assert _smith_on(three_day_df, td.Chelmsford21stAt1805)["TrainerWinPercentage"] == pytest.approx(0.0)


def test_win_percentage_with_wins(three_day_df):
    CalculateTrainerStats().process_race_data(three_day_df)
    # day3 history: day1(2nd) + day2(1st) → 1/2 = 0.5
    assert _smith_on(three_day_df, td.Nottingham22ndAt1815)["TrainerWinPercentage"] == pytest.approx(0.5)


def test_top3_percentage(three_day_df):
    CalculateTrainerStats().process_race_data(three_day_df)
    # day3 history: day1(2nd<4) + day2(1st<4) → 2/2 = 1.0
    assert _smith_on(three_day_df, td.Nottingham22ndAt1815)["TrainerTop3Percentage"] == pytest.approx(1.0)


def test_avg_relative_finishing_position(three_day_df):
    CalculateTrainerStats().process_race_data(three_day_df)
    # day1=2nd/2=1.0, day2=1st/2=0.5 → mean=0.75
    assert _smith_on(three_day_df, td.Nottingham22ndAt1815)["TrainerAvgRelFinishingPosition"] == pytest.approx(0.75)


def test_incremental_processing_across_days(three_day_df):
    CalculateTrainerStats().process_race_data(three_day_df)
    day1 = _smith_on(three_day_df, td.Ballinrobe20thAt1515)
    day3 = _smith_on(three_day_df, td.Nottingham22ndAt1815)
    assert day1["TrainerNumberOfPriorRaces"] == pytest.approx(1.0)  # default (no history)
    assert day3["TrainerNumberOfPriorRaces"] == 2  # 2 prior races
