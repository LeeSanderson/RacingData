import pandas as pd

from race_analytics.algorithms.base import FieldPredictorBaseAlgorithm
from race_analytics.algorithms.confidence_gate import ConfidenceGate
from race_analytics.algorithms.race_rules_gate import RaceRulesGate
from race_analytics.features.race_data import RaceData


class GatedClassifier(FieldPredictorBaseAlgorithm):
    """Decorator that wraps any FieldPredictorBaseAlgorithm with a confidence gate and hard race-rules gate.

    Filter A (confidence gate): calibrates from training-window in-sample predictions;
    threshold set so that `coverage` fraction of training races are kept.
    Filter B (race rules gate): hard exclusions — sprints (<6f) and Class 6 races.
    A race is bet only if it passes both gates.

    Calibration runs the inner over the *same* RaceData it was trained on — no
    flat → decomposed → re-encode round trip, and no `datetime.today()` skew (the
    in-sample features are the fold-date training features, not as-of-today stats).
    `fit`/`predict_field` also accept the legacy calling shapes (a flat training frame,
    four serving frames) until the harness is migrated in issue 007.
    """

    def __init__(self, inner: FieldPredictorBaseAlgorithm, metric: str = "top_prob", coverage: float = 0.7):
        super().__init__(inner.max_horses)
        self._inner = inner
        self._confidence_gate = ConfidenceGate(metric)
        self._rules_gate = RaceRulesGate()
        self._coverage = coverage

    def get_confidence_gate(self) -> ConfidenceGate:
        return self._confidence_gate

    def fit(self, data) -> None:
        if not isinstance(data, RaceData):
            data = self._training_data_from_legacy(data)
        self._inner.fit(data)
        self._calibrate(self._inner.predict_field(data))

    def _calibrate(self, training_field: pd.DataFrame) -> None:
        if training_field.empty or "WinProbability" not in training_field.columns:
            return
        gate = self._confidence_gate
        race_scores = training_field.groupby("RaceId")["WinProbability"].apply(gate.score).tolist()
        gate.calibrate(race_scores, self._coverage)

    def predict_field(self, data, horse_stats=None, jockey_stats=None, trainer_stats=None) -> pd.DataFrame:
        field = self._inner_field(data, horse_stats, jockey_stats, trainer_stats)
        field = self._apply_rules_gate(field, self._race_frame(data))
        return self._apply_confidence_gate(field)

    def predict_field_unfiltered(self, data, horse_stats=None, jockey_stats=None, trainer_stats=None) -> pd.DataFrame:
        """Field with rules gate only — no confidence gate. For ROI-vs-coverage frontier."""
        field = self._inner_field(data, horse_stats, jockey_stats, trainer_stats)
        return self._apply_rules_gate(field, self._race_frame(data))

    def _inner_field(self, data, horse_stats, jockey_stats, trainer_stats) -> pd.DataFrame:
        if isinstance(data, RaceData):
            return self._inner.predict_field(data)
        return self._inner.predict_field(data, horse_stats, jockey_stats, trainer_stats)

    @staticmethod
    def _race_frame(data) -> pd.DataFrame:
        """The frame the rules gate reads race-level attributes from."""
        return data.frame if isinstance(data, RaceData) else data

    def _apply_rules_gate(self, field: pd.DataFrame, races: pd.DataFrame) -> pd.DataFrame:
        if field.empty:
            return field
        excluded = self._rules_gate.excluded_race_ids(races)
        if not excluded:
            return field
        return field[~field["RaceId"].isin(excluded)].copy()

    def _apply_confidence_gate(self, field: pd.DataFrame) -> pd.DataFrame:
        if field.empty or "WinProbability" not in field.columns:
            return field
        gate = self._confidence_gate
        race_scores = field.groupby("RaceId")["WinProbability"].apply(gate.score)
        kept = race_scores[race_scores >= gate.threshold].index
        return field[field["RaceId"].isin(kept)].copy()
