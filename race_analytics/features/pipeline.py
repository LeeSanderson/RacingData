import gc
import pandas as pd

from race_analytics.features.transforms import (
    encode_surfaces,
    encode_going,
    encode_race_type,
    calculate_speed,
    clean_weight,
    calculate_horse_count,
)
from race_analytics.features.race_filters import CalculateRacesWithKnownHorsesAndJockeys
from race_analytics.features.horse_stats import CalculateHorsesStats, extract_horse_stats
from race_analytics.features.jockey_stats import CalculateJockeyStats, extract_jockey_stats
from race_analytics.features.trainer_stats import CalculateTrainerStats, extract_trainer_stats


class FeaturePipeline:

    def __init__(self) -> None:
        self._race_features: pd.DataFrame | None = None
        self._batch_counter = 0

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        self._batch_counter += 1
        batch_id = self._batch_counter

        df = df.copy()
        df["Wins"] = (df["FinishingPosition"] == 1).astype(int)
        df = encode_surfaces(df)
        df = encode_going(df)
        df = encode_race_type(df)
        df = calculate_speed(df)
        df = clean_weight(df)
        df = calculate_horse_count(df)
        df["_batch_id"] = batch_id

        if self._race_features is not None:
            combined = (
                pd.concat([self._race_features, df], ignore_index=True)
                .sort_values("Off")
                .reset_index(drop=True)
            )
        else:
            combined = df.sort_values("Off").reset_index(drop=True)

        CalculateRacesWithKnownHorsesAndJockeys().process_race_data(combined)
        gc.collect()
        CalculateHorsesStats().process_race_data(combined)
        gc.collect()
        CalculateJockeyStats().process_race_data(combined)
        gc.collect()
        CalculateTrainerStats().process_race_data(combined)
        gc.collect()

        result = combined[combined["_batch_id"] == batch_id].drop("_batch_id", axis=1).copy()
        self._race_features = combined.drop("_batch_id", axis=1)
        return result

    def save_race_features(self, path: str) -> None:
        self._race_features.to_csv(path, index=False)

    def save_horse_stats(self, path: str) -> None:
        extract_horse_stats(self._race_features).to_csv(path, index=False)

    def save_jockey_stats(self, path: str) -> None:
        extract_jockey_stats(self._race_features).to_csv(path, index=False)

    def save_trainer_stats(self, path: str) -> None:
        extract_trainer_stats(self._race_features).to_csv(path, index=False)
