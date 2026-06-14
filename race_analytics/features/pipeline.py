import gc

import pandas as pd

from race_analytics.features.horse_stats import (
    CalculateHorsesStats,
    extract_horse_stats,
)
from race_analytics.features.jockey_stats import (
    CalculateJockeyStats,
    extract_jockey_stats,
)
from race_analytics.features.race_filters import CalculateRacesWithKnownHorsesAndJockeys
from race_analytics.features.trainer_stats import (
    CalculateTrainerStats,
    extract_trainer_stats,
)
from race_analytics.features.transforms import (
    calculate_age_features,
    calculate_code_switch,
    calculate_distance_change,
    calculate_draw_features,
    calculate_horse_count,
    calculate_is_handicap,
    calculate_race_class,
    calculate_speed,
    calculate_surface_switch,
    calculate_weight_change,
    clean_weight,
    encode_age_band,
    encode_going,
    encode_pattern,
    encode_race_type,
    encode_sex_restriction,
    encode_surfaces,
)


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
        combined = calculate_weight_change(combined)
        combined = calculate_distance_change(combined)
        combined = calculate_surface_switch(combined)
        combined = calculate_code_switch(combined)
        combined = calculate_race_class(combined)
        combined = calculate_age_features(combined)
        combined = encode_pattern(combined)
        combined = calculate_is_handicap(combined)
        combined = encode_age_band(combined)
        combined = encode_sex_restriction(combined)
        combined = calculate_draw_features(combined)
        CalculateJockeyStats().process_race_data(combined)
        gc.collect()
        CalculateTrainerStats().process_race_data(combined)
        gc.collect()

        result = (
            combined[combined["_batch_id"] == batch_id].drop("_batch_id", axis=1).copy()
        )
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
