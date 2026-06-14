import pandas as pd

import tests.utils.test_data as td
from race_analytics.features.race_filters import CalculateRacesWithKnownHorsesAndJockeys

# --- helpers ---


def _make_df(*race_results):
    return pd.DataFrame(list(race_results))


# --- tests ---


def test_first_day_races_are_never_known():
    df = _make_df(
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.ComeSeptember, td.SimonTorrens),
    )
    CalculateRacesWithKnownHorsesAndJockeys().process_race_data(df)
    assert df["KnownHorseAndJockey"].tolist() == [False, False]


def test_race_with_all_known_horses_and_jockeys_is_marked_known():
    df = _make_df(
        # Day 1: establish history
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.ComeSeptember, td.SimonTorrens),
        # Day 2: same horses and jockeys → all known
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.SimonTorrens),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.ComeSeptember, td.PaulTown),
    )
    CalculateRacesWithKnownHorsesAndJockeys().process_race_data(df)
    assert df["KnownHorseAndJockey"].iloc[2]
    assert df["KnownHorseAndJockey"].iloc[3]


def test_race_with_unknown_horse_is_not_marked_known():
    df = _make_df(
        # Day 1: only SecretSecret/PaulTown seen
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown),
        # Day 2: LaylaDaffodil is a new horse → whole race unknown
        td.RaceResult.new(td.Chelmsford21stAt1805, td.LaylaDaffodil, td.PaulTown),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.SimonTorrens),
    )
    CalculateRacesWithKnownHorsesAndJockeys().process_race_data(df)
    assert not df["KnownHorseAndJockey"].iloc[1]
    assert not df["KnownHorseAndJockey"].iloc[2]


def test_race_with_unknown_jockey_is_not_marked_known():
    df = _make_df(
        # Day 1: SecretSecret/PaulTown and ComeSeptember/SimonTorrens seen
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.ComeSeptember, td.SimonTorrens),
        # Day 2: ShaneFitzgerald is a new jockey → whole race unknown
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SecretSecret, td.ShaneFitzgerald),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.ComeSeptember, td.PaulTown),
    )
    CalculateRacesWithKnownHorsesAndJockeys().process_race_data(df)
    assert not df["KnownHorseAndJockey"].iloc[2]
    assert not df["KnownHorseAndJockey"].iloc[3]


def test_incremental_processing_updates_correctly_across_days():
    """Unknown on day 1; fully known by day 3 as prior data accumulates."""
    df = _make_df(
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.SecretSecret, td.PaulTown),
        td.RaceResult.new(td.Ballinrobe20thAt1515, td.ComeSeptember, td.SimonTorrens),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.DuckAndVanish, td.PhilipDonovan),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.ComeSeptember, td.PaulTown),
        td.RaceResult.new(td.Chelmsford21stAt1805, td.SelfAssessed, td.KevinSexton),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.SecretSecret, td.PhilipDonovan),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.ComeSeptember, td.KevinSexton),
        td.RaceResult.new(td.Nottingham22ndAt1815, td.SelfAssessed, td.SimonTorrens),
    )
    CalculateRacesWithKnownHorsesAndJockeys().process_race_data(df)
    expected = [False, False, False, False, False, True, True, True]
    assert df["KnownHorseAndJockey"].tolist() == expected
