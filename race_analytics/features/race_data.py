"""Canonical, fully-engineered representation of a set of races.

`RaceData` is ONE flat frame (one row per horse-in-race) with every feature column
already materialised by the canonical transform chain. It is the single shape that
will flow through `fit()`, `predict_field()`, and gate calibration as the algorithm
subsystem migrates (see `issues/001-unify-prediction-data-path-racedata.md`).

`RaceDataBuilder` is the single home of the merge + transform chain. It joins a race
card to per-entity stats — extracted from a history frame (`build_serving`) or supplied
pre-computed (`build_serving_from_stats`) — and runs the canonical feature chain once.
Day-since features are computed against an explicit `as_of`, never `datetime.today()`.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from race_analytics.features.horse_stats import extract_horse_stats
from race_analytics.features.jockey_stats import extract_jockey_stats
from race_analytics.features.trainer_stats import extract_trainer_stats
from race_analytics.features.transforms import (
    calculate_age_features,
    calculate_code_switch,
    calculate_distance_change,
    calculate_draw_features,
    calculate_is_handicap,
    calculate_race_class,
    calculate_surface_switch,
    calculate_weight_change,
    encode_age_band,
    encode_going,
    encode_headgear,
    encode_pattern,
    encode_race_type,
    encode_sex_restriction,
    encode_surfaces,
)

_LABEL_COLUMNS = ("Wins", "Speed", "FinishingPosition")
_ONE_DAY = np.timedelta64(1, "D")


def _add_race_context(df: pd.DataFrame, extra_cols: Iterable[str] = ()) -> pd.DataFrame:
    """Add HorseCount and per-race Rel* columns. Mirrors the helper in
    binary_win_classifier.py so the canonical chain matches the live pipeline."""
    df = df.copy()
    if "HorseCount" not in df.columns:
        df["HorseCount"] = df.groupby("RaceId")["HorseId"].transform("count")
    for col in extra_cols:
        if col in df.columns:
            df[f"Rel{col}"] = df[col] - df.groupby("RaceId")[col].transform("mean")
    return df


# The canonical feature-engineering chain — declared ONCE, in the exact order the
# active win-classifier path (BinaryWinClassifierAlgorithm._run_prediction) applies
# it. Each callable takes and returns a DataFrame.
CANONICAL_TRANSFORMS = (
    encode_surfaces,
    encode_going,
    encode_race_type,
    calculate_weight_change,
    calculate_distance_change,
    calculate_surface_switch,
    calculate_code_switch,
    calculate_race_class,
    calculate_age_features,
    encode_pattern,
    calculate_is_handicap,
    encode_age_band,
    encode_sex_restriction,
    encode_headgear,
    _add_race_context,
    calculate_draw_features,
)


def _apply_canonical_chain(frame: pd.DataFrame) -> pd.DataFrame:
    for transform in CANONICAL_TRANSFORMS:
        frame = transform(frame)
    return frame


@dataclass(frozen=True)
class RaceData:
    """Immutable handle over a fully-engineered race frame.

    Invariants (guaranteed by RaceDataBuilder):
      * the encode_*/calculate_* chain has run exactly once, in canonical order;
      * DaysRested / DaysSinceJockeyLastRaced are clamped to <= 10;
      * `as_of` is the date features were computed 'as of' (fold date for training,
        serving date for prediction) — any today-relative logic reads this.
    """

    frame: pd.DataFrame
    as_of: pd.Timestamp
    max_horses: int = 10

    @property
    def has_labels(self) -> bool:
        """True iff a training label column is present (absent at serving time)."""
        return any(col in self.frame.columns for col in _LABEL_COLUMNS)

    def feature_frame(self, feature_cols: list[str]) -> pd.DataFrame:
        """The columns the estimator consumes, in the requested order."""
        return self.frame[list(feature_cols)]  # pyright: ignore[reportReturnType]  # column-list index yields DataFrame

    def with_columns(self, **new_cols: Any) -> RaceData:
        """Copy + add/overwrite columns (e.g. LastProxyTSR, recency weights)."""
        frame = self.frame.copy()
        for name, values in new_cols.items():
            frame[name] = values
        return replace(self, frame=frame)

    def subset(self, mask: pd.Series | pd.DataFrame | np.ndarray) -> RaceData:
        """Copy + row filter (e.g. an in-pipeline race gate)."""
        return replace(self, frame=self.frame[mask].copy())


class RaceDataBuilder:
    """The single place the merge + feature-transform chain runs."""

    def build_serving_from_stats(
        self,
        card: pd.DataFrame,
        horse_stats: pd.DataFrame,
        jockey_stats: pd.DataFrame,
        trainer_stats: pd.DataFrame | None,
        as_of: pd.Timestamp,
        max_horses: int = 10,
    ) -> RaceData:
        """Build serving RaceData from a card + pre-computed per-entity stats frames.

        Joins the stats onto the card, derives DaysRested / DaysSinceJockeyLastRaced
        against `as_of` (clamped to <= 10), and runs the canonical feature chain.
        Used directly when stats are already materialised (e.g. predict.py reads the
        Horse/Jockey/Trainer_Stats CSVs) and by `build_serving` after it extracts them.
        """
        today = np.datetime64(as_of)
        races = card

        merged = races.copy().merge(horse_stats, how="left", on=["HorseId"])
        merged["DaysRested"] = np.ceil(
            (today - pd.to_datetime(merged["LastOff"])) / _ONE_DAY
        )
        merged.loc[merged["DaysRested"] > 10, "DaysRested"] = 10
        merged = merged.drop("LastOff", axis=1, errors="ignore")

        merged = merged.merge(jockey_stats, how="left", on=["JockeyId"])
        merged["DaysSinceJockeyLastRaced"] = np.ceil(
            (today - pd.to_datetime(merged["LastOff"])) / _ONE_DAY
        )
        merged.loc[
            merged["DaysSinceJockeyLastRaced"] > 10, "DaysSinceJockeyLastRaced"
        ] = 10
        merged = merged.drop("LastOff", axis=1, errors="ignore")

        if trainer_stats is not None:
            merged = merged.merge(trainer_stats, how="left", on=["TrainerId"])

        merged = _apply_canonical_chain(merged)
        return RaceData(frame=merged, as_of=pd.Timestamp(as_of), max_horses=max_horses)  # pyright: ignore[reportArgumentType]  # Timestamp ctor return includes NaTType arm

    def build_serving(
        self,
        card: pd.DataFrame,
        history: RaceData | pd.DataFrame,
        as_of: pd.Timestamp,
        max_horses: int = 10,
    ) -> RaceData:
        """Join today's `card` to per-entity stats extracted from `history` and run
        the canonical chain. `history` is a RaceData or an enriched race_history frame."""
        hist = history.frame if isinstance(history, RaceData) else history
        horse_stats = extract_horse_stats(hist)
        jockey_stats = extract_jockey_stats(hist)
        trainer_stats = (
            extract_trainer_stats(hist) if "TrainerId" in hist.columns else None
        )
        return self.build_serving_from_stats(
            card, horse_stats, jockey_stats, trainer_stats, as_of, max_horses
        )

    def build_training(
        self, raw: pd.DataFrame, as_of: pd.Timestamp, max_horses: int = 10
    ) -> RaceData:
        """Build training RaceData (labels retained) from an enriched race_history
        frame. Stats are already columns, so this runs the canonical chain directly,
        clamping the day-since features exactly as the legacy fit() does."""
        frame = raw.copy()
        for col in ("DaysRested", "DaysSinceJockeyLastRaced"):
            if col in frame.columns:
                frame.loc[frame[col] > 10, col] = 10
        frame = _apply_canonical_chain(frame)
        return RaceData(frame=frame, as_of=pd.Timestamp(as_of), max_horses=max_horses)  # pyright: ignore[reportArgumentType]  # Timestamp ctor return includes NaTType arm

    def wrap_training(self, enriched: pd.DataFrame, max_horses: int = 10) -> RaceData:
        """Wrap an already-engineered flat training frame (the output of the harness's
        `_engineer_features`) as a RaceData WITHOUT re-running the canonical chain.

        Unlike `build_training`, this does NOT re-encode: `_engineer_features` produces
        a frame whose feature set deliberately omits WeightChange/DistanceChange/
        SurfaceSwitch/CodeSwitch, and re-running the chain would add them — changing the
        columns the estimator is fitted on. This only clamps the day-since features (the
        RaceData invariant) and stamps `as_of` as the fold date (one day past the last
        race), used by recency weighting. It is the single home of the training-frame
        wrap shared by the harness and the algorithm base's legacy fit adapter."""
        frame = enriched.copy()
        for col in ("DaysRested", "DaysSinceJockeyLastRaced"):
            if col in frame.columns:
                frame.loc[frame[col] > 10, col] = 10
        if "Off" in frame.columns:
            as_of = pd.to_datetime(frame["Off"]).max().normalize() + pd.Timedelta(
                days=1
            )
        else:
            as_of = pd.Timestamp(datetime.today())
        return RaceData(frame=frame, as_of=as_of, max_horses=max_horses)  # pyright: ignore[reportArgumentType]  # Off.max() is a Timestamp at runtime
