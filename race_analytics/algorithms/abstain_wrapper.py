import pandas as pd

from race_analytics.algorithms.base import REQUIRED_PREDICTORS
from race_analytics.algorithms.binary_win_classifier import _add_race_context
from race_analytics.algorithms.confidence_gate import ConfidenceGate
from race_analytics.algorithms.proxy_tsr_xgboost import (
    ProxyTSRXGBoostAlgorithm,
    RecencyWeightedProxyTSRAlgorithm,
    WeightedPositionProxyTSRAlgorithm,
)
from race_analytics.algorithms.race_rules_gate import RaceRulesGate


class AbstainWrapperAlgorithm(ProxyTSRXGBoostAlgorithm):
    """ProxyTSRXGBoostAlgorithm with confidence-gate + hard-race-rules abstain layer.

    Filter A (confidence gate): calibrates from training-window in-sample predictions;
    threshold set so that `coverage` fraction of training races are kept.
    Filter B (race rules gate): hard exclusions — sprints (<6f) and Class 6 races.
    A race is bet only if it passes both gates.
    """

    def __init__(
        self,
        metric: str = "top_prob",
        coverage: float = 0.7,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._confidence_gate = ConfidenceGate(metric)
        self._rules_gate = RaceRulesGate()
        self._coverage = coverage
        self._calib_train_df: pd.DataFrame | None = None

    def get_confidence_gate(self) -> ConfidenceGate:
        return self._confidence_gate

    def _prepare_training_df(self, train_df: pd.DataFrame) -> pd.DataFrame:
        df = super()._prepare_training_df(train_df)
        self._calib_train_df = df.copy()
        return df

    def fit(self, train_df: pd.DataFrame) -> None:
        super().fit(train_df)
        self._calibrate()
        self._calib_train_df = None  # free memory

    def _calibrate(self) -> None:
        """Calibrate confidence gate from in-sample training predictions."""
        if self._calib_train_df is None or self._calib_train_df.empty:
            return
        if not self._feature_cols or "RaceId" not in self._calib_train_df.columns:
            return
        df = _add_race_context(self._calib_train_df, self.extra_nan_tolerant_features)
        available = [c for c in self._feature_cols if c in df.columns]
        required = [c for c in REQUIRED_PREDICTORS if c in df.columns]
        data = df[["RaceId"] + available].dropna(subset=required).copy()
        if data.empty:
            return
        data = data.assign(WinProbability=self._compute_win_scores(data, available))
        gate = self._confidence_gate
        race_scores = (
            data.groupby("RaceId")["WinProbability"].apply(gate.score).tolist()
        )
        gate.calibrate(race_scores, self._coverage)

    def predict_field(
        self,
        races: pd.DataFrame,
        horse_stats: pd.DataFrame,
        jockey_stats: pd.DataFrame,
        trainer_stats: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        field = super().predict_field(races, horse_stats, jockey_stats, trainer_stats)
        field = self._apply_rules_gate(field, races)
        return self._apply_confidence_gate(field)

    def predict_field_unfiltered(
        self,
        races: pd.DataFrame,
        horse_stats: pd.DataFrame,
        jockey_stats: pd.DataFrame,
        trainer_stats: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """Field with rules gate but without confidence gating — for ROI-vs-coverage frontier."""
        field = ProxyTSRXGBoostAlgorithm.predict_field(
            self, races, horse_stats, jockey_stats, trainer_stats
        )
        return self._apply_rules_gate(field, races)

    def predict(
        self,
        races: pd.DataFrame,
        horse_stats: pd.DataFrame,
        jockey_stats: pd.DataFrame,
        trainer_stats: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        field = self.predict_field(races, horse_stats, jockey_stats, trainer_stats)
        if field.empty or "PredictedRank" not in field.columns:
            return pd.DataFrame(columns=["RaceId", "HorseId"])
        return (
            field[field["PredictedRank"] == 1][["RaceId", "HorseId"]]
            .drop_duplicates(subset=["RaceId"])
            .reset_index(drop=True)
        )

    def _apply_rules_gate(
        self, field: pd.DataFrame, races: pd.DataFrame
    ) -> pd.DataFrame:
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


class AbstainWrapperGapAlgorithm(AbstainWrapperAlgorithm):
    """AbstainWrapperAlgorithm using gap metric (top_prob - second_prob) at 50% coverage.

    A wide gap signals the model sees a clear standout; a narrow gap signals a
    genuinely contested race. Post-hoc analysis on 2,330-race eval CSV showed gap
    consistently dominates top_prob at coverage ≤ 65% after the rules gate is applied.
    """

    def __init__(self, **kwargs):
        super().__init__(metric="gap", coverage=0.5, **kwargs)


class AbstainWeightedPositionAlgorithm(
    AbstainWrapperAlgorithm, WeightedPositionProxyTSRAlgorithm
):
    """AbstainWrapperAlgorithm with position-based sample weighting (1/FinishingPosition)."""


class AbstainRecencyWeightedAlgorithm(
    AbstainWrapperAlgorithm, RecencyWeightedProxyTSRAlgorithm
):
    """AbstainWrapperAlgorithm with exponential decay sample weighting."""
