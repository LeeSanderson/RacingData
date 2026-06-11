import pandas as pd

from race_analytics.algorithms.base import FieldPredictorBaseAlgorithm
from race_analytics.algorithms.win_classifier import WinClassifier


class SplitDisciplineWinClassifier(WinClassifier):
    """WinClassifier with separate flat and jump sub-models.

    Trains distinct WinClassifier instances for flat and jump races, routing
    each prediction to the appropriate sub-model. Falls back to a model trained
    on all data when a sub-model has fewer than MIN_RACES unique races.

    The inner_class parameter allows cross-axis composition (e.g. wrapping a
    RecencyWeightedWinClassifier for each discipline sub-model).
    """

    MIN_RACES = 100

    def __init__(self, inner_class: type[FieldPredictorBaseAlgorithm] = WinClassifier, max_horses: int = 10):
        super().__init__(max_horses=max_horses)
        self._flat_model = inner_class(max_horses=max_horses)
        self._jumps_model = inner_class(max_horses=max_horses)
        self._fallback_model = inner_class(max_horses=max_horses)
        self._flat_available = False
        self._jumps_available = False

    def fit(self, train_df: pd.DataFrame) -> None:
        flat_df, jumps_df = self._split_train_by_race_type(train_df)

        self._flat_available = (
            flat_df["RaceId"].nunique() >= self.MIN_RACES if not flat_df.empty else False
        )
        self._jumps_available = (
            jumps_df["RaceId"].nunique() >= self.MIN_RACES if not jumps_df.empty else False
        )

        if self._flat_available:
            self._flat_model.fit(flat_df)
        if self._jumps_available:
            self._jumps_model.fit(jumps_df)
        if not self._flat_available or not self._jumps_available:
            self._fallback_model.fit(train_df)

        super().fit(train_df)

    def _split_train_by_race_type(
        self, df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        if "RaceType_Flat" in df.columns:
            mask = df["RaceType_Flat"] == 1
        elif "RaceType" in df.columns:
            mask = df["RaceType"] == "Flat"
        else:
            mask = pd.Series(False, index=df.index)
        return df[mask].copy(), df[~mask].copy()

    def predict_field(
        self,
        races: pd.DataFrame,
        horse_stats: pd.DataFrame,
        jockey_stats: pd.DataFrame,
        trainer_stats: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        if "RaceType" not in races.columns:
            return self._fallback_model.predict_field(
                races, horse_stats, jockey_stats, trainer_stats
            )

        flat_mask = races["RaceType"] == "Flat"
        flat_races = races[flat_mask]
        jumps_races = races[~flat_mask]

        parts = []
        if not flat_races.empty:
            m = self._flat_model if self._flat_available else self._fallback_model
            parts.append(m.predict_field(flat_races, horse_stats, jockey_stats, trainer_stats))
        if not jumps_races.empty:
            m = self._jumps_model if self._jumps_available else self._fallback_model
            parts.append(m.predict_field(jumps_races, horse_stats, jockey_stats, trainer_stats))

        non_empty = [p for p in parts if not p.empty]
        if not non_empty:
            return pd.DataFrame(columns=["RaceId", "HorseId"])
        return pd.concat(non_empty, ignore_index=True)

