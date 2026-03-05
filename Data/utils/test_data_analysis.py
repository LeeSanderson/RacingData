import pytest
import pandas as pd
import utils.test_data as td

from utils.data_analysis import (
    calculateHorsesPerRace,
    CalculateRacesWithKnownHorsesAndJockeys)

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

def test_CalculateRacesWithKnownHorsesAndJockeys():
    processor = CalculateRacesWithKnownHorsesAndJockeys()

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
    processor.process_race_data(df)
    expected_known = [False, False, False, False, False, True, True, True]
    assert df["KnownHorseAndJockey"].tolist() == expected_known
