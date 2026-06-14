import pandas as pd

from race_analytics.algorithms.market_favourite import MarketFavouriteBaseline


def _odds_df(rows):
    return pd.DataFrame(rows, columns=["RaceId", "HorseId", "DecimalOdds"])


def test_returns_raceId_and_horseId_columns():
    df = _odds_df([(1, 101, 3.0), (1, 102, 5.0)])
    result = MarketFavouriteBaseline().predict([1], df)
    assert list(result.columns) == ["RaceId", "HorseId"]


def test_picks_horse_with_lowest_odds():
    df = _odds_df([(1, 101, 5.0), (1, 102, 2.0), (1, 103, 8.0)])
    result = MarketFavouriteBaseline().predict([1], df)
    assert result.iloc[0]["HorseId"] == 102


def test_returns_one_winner_per_race():
    df = _odds_df([(1, 101, 3.0), (1, 102, 5.0), (2, 201, 4.0), (2, 202, 2.0)])
    result = MarketFavouriteBaseline().predict([1, 2], df)
    assert len(result) == 2
    assert set(result["RaceId"]) == {1, 2}


def test_skips_race_with_missing_odds():
    df = _odds_df([(1, 101, 3.0), (1, 102, None), (2, 201, 4.0), (2, 202, 2.0)])
    result = MarketFavouriteBaseline().predict([1, 2], df)
    assert len(result) == 1
    assert result.iloc[0]["RaceId"] == 2


def test_only_evaluates_specified_race_ids():
    df = _odds_df([(1, 101, 3.0), (1, 102, 5.0), (2, 201, 4.0), (2, 202, 2.0)])
    result = MarketFavouriteBaseline().predict([1], df)
    assert len(result) == 1
    assert result.iloc[0]["RaceId"] == 1


def test_returns_empty_dataframe_when_no_valid_races():
    df = _odds_df([(1, 101, None), (1, 102, 3.0)])
    result = MarketFavouriteBaseline().predict([1], df)
    assert list(result.columns) == ["RaceId", "HorseId"]
    assert len(result) == 0
