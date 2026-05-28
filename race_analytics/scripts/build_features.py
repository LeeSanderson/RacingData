import argparse
import os

from race_analytics.features.loader import load_results
from race_analytics.features.pipeline import FeaturePipeline

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(_SCRIPTS_DIR)), "Data")

# Limit to the current month plus the previous 6 months. Loading the full
# history is unnecessary for feature building and is much slower.
_TRAINING_MONTHS = 7


def build_features(
    data_path: str | None = None, months: int = _TRAINING_MONTHS
) -> None:
    if data_path is None:
        data_path = _DATA_DIR

    print(f"Loading results (last {months} months)...")
    results = load_results(data_path, months=months)
    print(f"  Loaded {len(results)} rows")

    print("Processing features...")
    pipeline = FeaturePipeline()
    pipeline.process(results)

    print("Saving outputs...")
    pipeline.save_race_features(os.path.join(data_path, "Race_Features.csv"))
    pipeline.save_horse_stats(os.path.join(data_path, "Horse_Stats.csv"))
    pipeline.save_jockey_stats(os.path.join(data_path, "Jockey_Stats.csv"))
    pipeline.save_trainer_stats(os.path.join(data_path, "Trainer_Stats.csv"))
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build feature CSVs from historical race results."
    )
    parser.add_argument("--data", default=None, help="Path to data directory")
    parser.add_argument(
        "--months",
        type=int,
        default=_TRAINING_MONTHS,
        help="Number of most-recent monthly Results files to load",
    )
    args = parser.parse_args()
    build_features(args.data, months=args.months)
