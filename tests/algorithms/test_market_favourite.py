from typing import Any

import pandas as pd

from race_analytics.algorithms.market_favourite import MarketFavouriteBaseline


def _odds_df(rows: list[tuple[Any, ...]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["RaceId", "HorseId", "DecimalOdds"])


def test_returns_raceId_and_horseId_columns() -> None:
    df = _odds_df([(1, 101, 3.0), (1, 102, 5.0)])
    result = MarketFavouriteBaseline().predict([1], df)
    assert list(result.columns) == ["RaceId", "HorseId"]


def test_picks_horse_with_lowest_odds() -> None:
    df = _odds_df([(1, 101, 5.0), (1, 102, 2.0), (1, 103, 8.0)])
    result = MarketFavouriteBaseline().predict([1], df)
    assert result.iloc[0]["HorseId"] == 102


def test_returns_one_winner_per_race() -> None:
    df = _odds_df([(1, 101, 3.0), (1, 102, 5.0), (2, 201, 4.0), (2, 202, 2.0)])
    result = MarketFavouriteBaseline().predict([1, 2], df)
    assert len(result) == 2
    assert set(result["RaceId"]) == {1, 2}


def test_skips_race_with_missing_odds() -> None:
    df = _odds_df([(1, 101, 3.0), (1, 102, None), (2, 201, 4.0), (2, 202, 2.0)])
    result = MarketFavouriteBaseline().predict([1, 2], df)
    assert len(result) == 1
    assert result.iloc[0]["RaceId"] == 2


def test_only_evaluates_specified_race_ids() -> None:
    df = _odds_df([(1, 101, 3.0), (1, 102, 5.0), (2, 201, 4.0), (2, 202, 2.0)])
    result = MarketFavouriteBaseline().predict([1], df)
    assert len(result) == 1
    assert result.iloc[0]["RaceId"] == 1


def test_returns_empty_dataframe_when_no_valid_races() -> None:
    df = _odds_df([(1, 101, None), (1, 102, 3.0)])
    result = MarketFavouriteBaseline().predict([1], df)
    assert list(result.columns) == ["RaceId", "HorseId"]
    assert len(result) == 0


def _odds_df_with_forecast(rows: list[tuple[Any, ...]]) -> pd.DataFrame:
    return pd.DataFrame(
        rows, columns=["RaceId", "HorseId", "DecimalOdds", "ForecastDecimalOdds"]
    )


def test_picks_favourite_by_resolved_odds_forecast_preferred() -> None:
    # SP alone makes 101 the favourite (2.0 vs 5.0), but 102 carries a forecast (1.5)
    # that is preferred over its SP. Resolved odds: 101=2.0, 102=1.5 -> 102 is the
    # favourite. Forecast flips the pick away from the SP-only choice.
    df = _odds_df_with_forecast([(1, 101, 2.0, float("nan")), (1, 102, 5.0, 1.5)])
    result = MarketFavouriteBaseline().predict([1], df)
    assert result.iloc[0]["HorseId"] == 102
