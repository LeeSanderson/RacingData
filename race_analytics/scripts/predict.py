import os
import argparse
import pandas as pd
from race_analytics.algorithms import ACTIVE_ALGORITHM

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)), "Data")

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
    "OfficialRating",
    "RacingPostRating",
    "TopSpeedRating",
]
_OUTPUT_COLS = ["RaceId", "CourseId", "CourseName", "Off", "HorseId", "HorseName"]


def predict(data_path: str | None = None, algorithm=None) -> pd.DataFrame:
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

    algorithm.fit(race_features)
    card = race_cards[[c for c in _RACE_CARD_COLS if c in race_cards.columns]].copy()
    winners = algorithm.predict(card, horse_stats, jockey_stats, trainer_stats)

    output_path = os.path.join(data_path, "TodaysPredictions.csv")

    if winners.empty:
        empty = pd.DataFrame(columns=_OUTPUT_COLS)
        empty.to_csv(output_path, index=False)
        return empty

    meta = race_cards[
        ["RaceId", "HorseId", "CourseId", "CourseName", "Off", "HorseName"]
    ].copy()
    predictions = pd.merge(winners, meta, on=["RaceId", "HorseId"], how="left")
    predictions = predictions.sort_values(["CourseName", "Off"])[
        _OUTPUT_COLS
    ].reset_index(drop=True)
    predictions.to_csv(output_path, index=False)
    return predictions


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=None)
    args = parser.parse_args()
    result = predict(args.data)
    print(f"Generated predictions for {len(result)} races")
    if not result.empty:
        print(result[["CourseName", "Off", "HorseName"]].to_string(index=False))
