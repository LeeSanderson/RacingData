import argparse
import os
from datetime import datetime

import pandas as pd

from race_analytics.algorithms import ACTIVE_ALGORITHM
from race_analytics.algorithms.base import FieldPredictor
from race_analytics.betting.staking import (
    MARKET_PROB,
    RESOLVED_ODDS,
    WIN_PROBABILITY,
    compute_stakes,
)
from race_analytics.features.market_prob import resolve_decimal_odds
from race_analytics.features.race_data import RaceDataBuilder

_STAKE = "Stake"

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)), "Data")

# No rating columns: ratings reach the algorithms only through the per-horse
# stats join (previous-race LastRace* ratings), never the card — see issues/prd.md.
_RACE_CARD_COLS = [
    "RaceId",
    "HorseId",
    "JockeyId",
    "TrainerId",
    "Surface",
    "Going",
    "RaceType",
    "DistanceInMeters",
    "WeightInPounds",
    "Class",
    "Age",
    "StallNumber",
    "Pattern",
    "RatingBand",
    "AgeBand",
    "SexRestriction",
    "HeadGear",
    # Not features: carried only so calculate_market_prob has its input at serve time.
    # On the live card the morning forecast already occupies DecimalOdds, so production
    # serves the forecast-derived MarketProb with no SP involved.
    "DecimalOdds",
    "ForecastDecimalOdds",
]
_OUTPUT_COLS = [
    "RaceId",
    "CourseId",
    "CourseName",
    "Off",
    "HorseId",
    "HorseName",
    "WinProbability",
    _STAKE,
]


def _attach_stakes(field: pd.DataFrame, serve_frame: pd.DataFrame) -> pd.DataFrame:
    """Add the advisory ``Stake`` column to the full scored field.

    Sourced from the serving frame so it works whatever columns the algorithm's
    ``predict_field`` chooses to return: the canonical chain has already
    materialized the de-overround ``MarketProb`` (the value-gate input) there, and
    the resolved forecast-when-present-else-SP gross odds (the Kelly payout input)
    come from ``resolve_decimal_odds`` over the same frame. Stakes are computed over
    the WHOLE field so the within-race probability normalization the value gate
    needs spans every runner, not just the published winner row.
    """
    field = field.reset_index(drop=True)
    if WIN_PROBABILITY not in field.columns:
        field[_STAKE] = 0.0
        return field
    if field.empty:
        field[_STAKE] = pd.Series(dtype=float)
        return field

    priced = serve_frame[["RaceId", "HorseId"]].copy()
    priced[MARKET_PROB] = serve_frame[MARKET_PROB]
    priced[RESOLVED_ODDS] = resolve_decimal_odds(serve_frame)
    priced = priced.drop_duplicates(subset=["RaceId", "HorseId"])

    staking_input = field[["RaceId", "HorseId", WIN_PROBABILITY]].merge(
        priced, on=["RaceId", "HorseId"], how="left"
    )
    field[_STAKE] = compute_stakes(staking_input).to_numpy()
    return field


def predict(
    data_path: str | None = None, algorithm: FieldPredictor | None = None
) -> pd.DataFrame:
    if data_path is None:
        data_path = _DATA_DIR
    if algorithm is None:
        algorithm = ACTIVE_ALGORITHM
    print(f"Using algorithm: {type(algorithm).__name__}")

    race_features = pd.read_csv(os.path.join(data_path, "Race_Features.csv"))
    horse_stats = pd.read_csv(os.path.join(data_path, "Horse_Stats.csv"))
    jockey_stats = pd.read_csv(os.path.join(data_path, "Jockey_Stats.csv"))
    trainer_stats = pd.read_csv(os.path.join(data_path, "Trainer_Stats.csv"))
    race_cards = pd.read_csv(os.path.join(data_path, "TodaysRaceCards.csv"))
    race_cards["Off"] = pd.to_datetime(race_cards["Off"], format="%m/%d/%Y %H:%M:%S")

    # Build the canonical RaceData and drive the algorithm through the FieldPredictor
    # contract. `wrap_training` wraps the enriched Race_Features frame;
    # `build_serving_from_stats` joins today's card to the precomputed per-entity stats
    # CSVs as-of now (the Stats CSVs are extract_*_stats(Race_Features), so this matches
    # build_serving over the same history).
    builder = RaceDataBuilder()
    algorithm.fit(builder.wrap_training(race_features, max_horses=algorithm.max_horses))

    card = race_cards[[c for c in _RACE_CARD_COLS if c in race_cards.columns]].copy()
    serve_data = builder.build_serving_from_stats(
        card,
        horse_stats,
        jockey_stats,
        trainer_stats,
        as_of=pd.Timestamp(datetime.today()),  # pyright: ignore[reportArgumentType]  # Timestamp ctor return includes NaTType arm
        max_horses=algorithm.max_horses,
    )
    field = algorithm.predict_field(serve_data)
    field = _attach_stakes(field, serve_data.frame)
    if field.empty or "PredictedRank" not in field.columns:
        winners = pd.DataFrame(columns=["RaceId", "HorseId"])
    else:
        winners = (
            field[field["PredictedRank"] == 1][  # pyright: ignore[reportCallIssue]  # column-list index narrows to DataFrame
                ["RaceId", "HorseId", "WinProbability", _STAKE]
            ]
            .drop_duplicates(subset=["RaceId"])  # pyright: ignore[reportAttributeAccessIssue]  # result is a DataFrame
            .reset_index(drop=True)
        )

    output_path = os.path.join(data_path, "TodaysPredictions.csv")

    if winners.empty:
        empty = pd.DataFrame(columns=_OUTPUT_COLS)
        empty.to_csv(output_path, index=False)
        return empty

    meta = race_cards[
        ["RaceId", "HorseId", "CourseId", "CourseName", "Off", "HorseName"]
    ].copy()
    predictions = winners.merge(meta, on=["RaceId", "HorseId"], how="left")
    out_cols = [c for c in _OUTPUT_COLS if c in predictions.columns]
    predictions = predictions.sort_values(["CourseName", "Off"])[out_cols].reset_index(
        drop=True
    )
    predictions.to_csv(output_path, index=False)
    return predictions  # pyright: ignore[reportReturnType]  # column-list index yields DataFrame


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=None)
    args = parser.parse_args()
    result = predict(args.data)
    print(f"Generated predictions for {len(result)} races")
    if not result.empty:
        print(result[["CourseName", "Off", "HorseName"]].to_string(index=False))
