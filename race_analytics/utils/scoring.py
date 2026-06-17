import pandas as pd

from race_analytics.features.market_prob import resolve_decimal_odds


def _valid(predictions: pd.DataFrame, results: pd.DataFrame) -> pd.DataFrame:
    merged = predictions.merge(results, on=["RaceId", "HorseId"], how="left")
    return merged[merged["ResultStatus"] == "CompletedRace"]  # pyright: ignore[reportReturnType]  # boolean-indexing a DataFrame returns a DataFrame


def accuracy(predictions: pd.DataFrame, results: pd.DataFrame) -> float:
    valid = _valid(predictions, results)
    if len(valid) == 0:
        return 0.0
    return (valid["FinishingPosition"] == 1).sum() / len(valid)


def roi(predictions: pd.DataFrame, results: pd.DataFrame) -> float:
    valid = _valid(predictions, results)
    if len(valid) == 0:
        return 0.0
    total_stakes = len(valid)
    # Value winners at resolved odds (forecast-when-present-else-SP) via the single
    # market-odds rule, so measurement matches the model's notion of "the market".
    # On historic SP-only data this equals DecimalOdds, so today's numbers are unchanged.
    resolved = resolve_decimal_odds(valid)
    winnings = resolved[valid["FinishingPosition"] == 1].sum()
    return float(winnings) - total_stakes
