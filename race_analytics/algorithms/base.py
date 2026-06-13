from abc import ABC, abstractmethod
from dataclasses import replace
from typing import ClassVar, Protocol, runtime_checkable
import numpy as np
import pandas as pd

from race_analytics.features.race_data import RaceData

REQUIRED_PREDICTORS = [
    "DistanceInMeters",
    "WeightInPounds",
    "Surface_AllWeather",
    "Surface_Dirt",
    "Surface_Turf",
    "Going_Firm",
    "Going_Good",
    "Going_Good_To_Firm",
    "Going_Good_To_Soft",
    "Going_Heavy",
    "Going_Soft",
    "RaceType_Flat",
    "RaceType_Hurdle",
    "RaceType_Other",
    "RaceType_SteepleChase",
    "LastRaceDistanceInMeters",
    "LastRaceWeightInPounds",
    "LastRaceSpeed",
    "DaysRested",
    "LastRaceAvgRelFinishingPosition",
    "LastRaceSurface_AllWeather",
    "LastRaceSurface_Dirt",
    "LastRaceSurface_Turf",
    "LastRaceGoing_Good",
    "LastRaceGoing_Good_To_Soft",
    "LastRaceGoing_Soft",
    "LastRaceGoing_Good_To_Firm",
    "LastRaceGoing_Firm",
    "LastRaceGoing_Heavy",
    "LastRaceRaceType_Other",
    "LastRaceRaceType_Hurdle",
    "LastRaceRaceType_SteepleChase",
    "LastRaceRaceType_Flat",
    "JockeyNumberOfPriorRaces",
    "DaysSinceJockeyLastRaced",
    "JockeyWinPercentage",
    "JockeyTop3Percentage",
    "JockeyAvgRelFinishingPosition",
    "TrainerNumberOfPriorRaces",
    "TrainerWinPercentage",
    "TrainerTop3Percentage",
    "TrainerAvgRelFinishingPosition",
    "IsFirstTimeHeadgear",
    "HasBlinkers",
    "HasCheekpieces",
    "HasTongueTie",
    "HasHood",
    "HasVisor",
    "HeadGearChanged",
]

OPTIONAL_PREDICTORS = [
    "Last3RaceAvgSpeed",
    "Last3RaceSpeedTrend",
    "Last3AvgRelFinishingPosition",
    "WeightChange",
    "DistanceChange",
    "HorseCount",
    "SurfaceSwitch",
    "CodeSwitch",
    "RaceClass",
    "Age",
    "RelAge",
    "DrawPct",
    "RelDraw",
    "IsHandicap",
    "Pattern_Group1",
    "Pattern_Group2",
    "Pattern_Group3",
    "Pattern_Listed",
    "Pattern_None",
    "AgeBand_2yo",
    "AgeBand_3yo",
    "AgeBand_3yoPlus",
    "AgeBand_4yoPlus",
    "AgeBand_None",
    "SexRestriction_F",
    "SexRestriction_FM",
    "SexRestriction_Open",
]

PREDICTORS = REQUIRED_PREDICTORS + OPTIONAL_PREDICTORS


class BaseAlgorithm(ABC):
    nan_tolerant_predictors: ClassVar[list[str]] = []

    def __init__(self, max_horses: int = 10):
        self.max_horses = max_horses

    @abstractmethod
    def fit(self, data: RaceData) -> None: ...

    @abstractmethod
    def predict(self, data: RaceData) -> pd.DataFrame: ...


@runtime_checkable
class FieldPredictor(Protocol):
    """The declared contract the harness programs against once migration completes
    (issue 007) — `fit`/`predict_field`/`predict` over a single RaceData."""

    max_horses: int

    def fit(self, data: RaceData) -> None: ...
    def predict_field(self, data: RaceData) -> pd.DataFrame: ...
    def predict(self, data: RaceData) -> pd.DataFrame: ...


@runtime_checkable
class AbstainCapable(Protocol):
    """Separately-declared capability for algorithms that can abstain — replaces the
    harness's reflective hasattr/getattr probing (issue 007)."""

    def predict_field_unfiltered(self, data): ...
    def get_confidence_gate(self): ...


class FieldPredictorBaseAlgorithm(BaseAlgorithm):
    """Convention-driven template that owns the shared prediction data-path.

    Produces, per race, a scored field with `score_col` and `PredictedRank`, then a
    top-1 pick. Subclasses supply only what varies — the estimator-fit and score
    hooks, plus optional prepare/gate/weight hooks.

    `fit`/`predict_field`/`predict` all take a single `RaceData`. The merge/encode lives
    in `RaceDataBuilder` and the complete-race/dropna/rank data-path lives here, so an
    algorithm never re-implements it.
    """

    # ── convention knobs (override by class assignment) ──
    label_col: ClassVar[str] = "Wins"
    score_col: ClassVar[str] = "WinProbability"
    return_full_field: ClassVar[bool] = True
    extra_nan_tolerant_features: ClassVar[list[str]] = []

    def __init__(self, max_horses: int = 10):
        super().__init__(max_horses)
        self._feature_cols: list[str] = []

    # ── variation-point hooks (identity / None / not-implemented defaults) ──
    def _prepare_training(self, data: RaceData) -> RaceData:
        return data

    def _prepare_serving(self, data: RaceData) -> RaceData:
        return data

    def _race_gate(self, data: RaceData) -> RaceData:
        return data

    def _sample_weight(self, frame: pd.DataFrame):
        return None

    def _fit_estimator(self, X: pd.DataFrame, frame: pd.DataFrame, sample_weight) -> None:
        raise NotImplementedError("engine subclasses must implement _fit_estimator")

    def _score(self, X: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError("engine subclasses must implement _score")

    # ── the one training data-path ──
    def fit(self, data: RaceData) -> None:
        data = self._prepare_training(data)
        self._feature_cols = self._select_features(data)
        train = self._dropna_required(data)
        self._fit_estimator(
            train.feature_frame(self._feature_cols),
            train.frame,
            self._sample_weight(train.frame),
        )

    # ── the one serving data-path ──
    def predict_field(self, data: RaceData) -> pd.DataFrame:
        if not self._feature_cols:
            return self._empty()
        data = self._prepare_serving(data)
        available = [c for c in self._feature_cols if c in data.frame.columns]
        original_counts = data.frame.groupby("RaceId")["HorseId"].count()
        predictable = self._keep_complete_races(self._dropna_required(data), original_counts)
        predictable = self._race_gate(predictable)
        if predictable.frame.empty:
            return self._empty()
        scores = self._score(predictable.feature_frame(available))
        field = self._rank_within_race(predictable.frame, scores)
        if not self.return_full_field:
            field = field[field["PredictedRank"] == 1].reset_index(drop=True)
        return field

    def predict(self, data: RaceData) -> pd.DataFrame:
        return self._top1(self.predict_field(data))

    def _add_race_context(self, data: RaceData) -> RaceData:
        """Materialise HorseCount and the per-race `Rel{col}` columns for the
        `extra_nan_tolerant_features`. Shared by every win-classifier family member so
        the relative-rating logic runs identically for all of them."""
        frame = data.frame.copy()
        if "HorseCount" not in frame.columns:
            frame["HorseCount"] = frame.groupby("RaceId")["HorseId"].transform("count")
        for col in self.extra_nan_tolerant_features:
            if col in frame.columns:
                frame[f"Rel{col}"] = frame[col] - frame.groupby("RaceId")[col].transform("mean")
        return replace(data, frame=frame)

    # ── shared helpers (implemented once) ──
    def _feature_universe(self) -> list[str]:
        extra = list(self.extra_nan_tolerant_features)
        rel_extra = [f"Rel{c}" for c in extra]
        return REQUIRED_PREDICTORS + OPTIONAL_PREDICTORS + extra + rel_extra

    def _select_features(self, data: RaceData) -> list[str]:
        return [c for c in self._feature_universe() if c in data.frame.columns]

    def _dropna_required(self, data: RaceData) -> RaceData:
        required = [
            c for c in REQUIRED_PREDICTORS
            if c in self._feature_cols
            and c not in self.nan_tolerant_predictors
            and c in data.frame.columns
        ]
        if data.has_labels and self.label_col in data.frame.columns:
            required = required + [self.label_col]
        if not required:
            return data
        mask = data.frame[required].notna().all(axis=1)
        return data.subset(mask)

    def _keep_complete_races(self, data: RaceData, original_counts: pd.Series) -> RaceData:
        pred_counts = data.frame.groupby("RaceId")["HorseId"].count()
        orig = original_counts.reindex(pred_counts.index)
        keep = pred_counts.index[
            (pred_counts.values == orig.values) & (orig.values <= self.max_horses)
        ]
        return data.subset(data.frame["RaceId"].isin(keep))

    def _rank_within_race(self, frame: pd.DataFrame, scores: np.ndarray) -> pd.DataFrame:
        out = frame.copy()
        out[self.score_col] = scores
        out["PredictedRank"] = out.groupby("RaceId")[self.score_col].rank(
            method="dense", ascending=False
        )
        return out

    @staticmethod
    def _empty() -> pd.DataFrame:
        return pd.DataFrame(columns=["RaceId", "HorseId"])

    def _top1(self, field: pd.DataFrame) -> pd.DataFrame:
        if field.empty or "PredictedRank" not in field.columns:
            return self._empty()
        return (
            field[field["PredictedRank"] == 1][["RaceId", "HorseId"]]
            .drop_duplicates(subset=["RaceId"])
            .reset_index(drop=True)
        )
