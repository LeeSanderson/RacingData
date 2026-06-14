import pandas as pd


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
    winnings = valid.loc[valid["FinishingPosition"] == 1, "DecimalOdds"].sum()
    return winnings - total_stakes
