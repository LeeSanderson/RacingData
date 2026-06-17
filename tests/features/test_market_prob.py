import pandas as pd
import pytest

from race_analytics.features.market_prob import (
    add_market_prob,
    resolve_decimal_odds,
)


def test_priced_race_is_normalized_and_overround_removed() -> None:
    # Decimal odds [2.0, 4.0] imply [0.5, 0.25] which sums to 0.75 (the overround).
    # Normalizing within the race removes it -> [0.6667, 0.3333], summing to 1.
    df = pd.DataFrame(
        {
            "RaceId": [1, 1],
            "HorseId": [10, 11],
            "DecimalOdds": [2.0, 4.0],
        }
    )
    result = add_market_prob(df)
    assert result["MarketProb"].tolist() == pytest.approx([2 / 3, 1 / 3])
    assert result["MarketProb"].sum() == pytest.approx(1.0)


def test_resolve_prefers_forecast_falls_back_to_sp() -> None:
    # Runner A has a forecast price (2.0) and an SP (3.0) -> forecast wins.
    # Runner B has no forecast (NaN) -> falls back to its SP (4.0).
    df = pd.DataFrame(
        {
            "RaceId": [1, 1],
            "HorseId": [10, 11],
            "ForecastDecimalOdds": [2.0, float("nan")],
            "DecimalOdds": [3.0, 4.0],
        }
    )
    resolved = resolve_decimal_odds(df)
    assert resolved.tolist() == pytest.approx([2.0, 4.0])


def test_unpriced_race_falls_back_to_uniform_prior() -> None:
    # No runner has a usable price (NaN forecast, non-positive/missing SP) -> every
    # runner takes the uniform prior 1/field_size, and the column stays dense.
    df = pd.DataFrame(
        {
            "RaceId": [1, 1, 1, 1],
            "HorseId": [10, 11, 12, 13],
            "ForecastDecimalOdds": [float("nan")] * 4,
            "DecimalOdds": [float("nan"), 0.0, float("nan"), float("nan")],
        }
    )
    result = add_market_prob(df)
    assert result["MarketProb"].notna().all()
    assert result["MarketProb"].tolist() == pytest.approx([0.25, 0.25, 0.25, 0.25])
    assert result["MarketProb"].sum() == pytest.approx(1.0)


def test_each_race_is_normalized_independently() -> None:
    # Race 1 has 2 runners, race 2 has 3 -> each RaceId must sum to 1 on its own.
    df = pd.DataFrame(
        {
            "RaceId": [1, 1, 2, 2, 2],
            "HorseId": [10, 11, 20, 21, 22],
            "DecimalOdds": [2.0, 4.0, 2.0, 4.0, 4.0],
        }
    )
    result = add_market_prob(df)
    for race_id in (1, 2):
        race = result[result["RaceId"] == race_id]
        assert race["MarketProb"].sum() == pytest.approx(1.0)
    # Race 2 implied [0.5, 0.25, 0.25] sums to 1.0 already -> unchanged.
    race2 = result[result["RaceId"] == 2]["MarketProb"].tolist()
    assert race2 == pytest.approx([0.5, 0.25, 0.25])


def test_void_runner_among_priced_stays_dense() -> None:
    # One runner is void (no price); the field has 3 runners so its implied is the
    # uniform prior 1/3. Implied totals 1/2 + 1/4 + 1/3 = 13/12, so MarketProb is each
    # implied / (13/12). The column must stay dense and still sum to 1.
    df = pd.DataFrame(
        {
            "RaceId": [1, 1, 1],
            "HorseId": [10, 11, 12],
            "DecimalOdds": [2.0, 4.0, float("nan")],
        }
    )
    result = add_market_prob(df)
    assert result["MarketProb"].notna().all()
    assert result["MarketProb"].tolist() == pytest.approx([6 / 13, 3 / 13, 4 / 13])
    assert result["MarketProb"].sum() == pytest.approx(1.0)
