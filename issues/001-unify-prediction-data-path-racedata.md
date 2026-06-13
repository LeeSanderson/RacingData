# 001 — Unify the prediction data-path on a canonical `RaceData` value object

**Status:** Proposed (parent RFC — decomposed into AFK slices below; **do not implement 001 directly**)
**Type:** Architecture / refactor (module deepening) — design/decision doc, HITL
**Scope:** `race_analytics/algorithms/`, `race_analytics/features/`, `race_analytics/scripts/evaluate.py`, `tests/`

## Decomposition (2026-06-13)

This RFC is the parent; the work is carried out by the dependency-ordered AFK slices below. Each is
behavior-preserving and leaves the suite green until the final cleanup:

1. `issues/002-racedata-value-object-and-builder.md` — `RaceData` + `RaceDataBuilder` + characterization (no algorithm touched)
2. `issues/003-deepen-fieldpredictor-engine.md` — deepen `FieldPredictorBaseAlgorithm` into the template engine + Protocols
3. `issues/004-migrate-win-classifier-family.md` — migrate the win-classifier family onto the hooks
4. `issues/005-migrate-regressor-family.md` — migrate the regressor family onto the engine
5. `issues/006-migrate-gated-classifier-calibration.md` — gate calibrates on the same `RaceData` (drop the round trip)
6. `issues/007-migrate-harness-evaluate-predict.md` — `evaluate.py` + `predict.py` on `RaceData` + the Protocol contract
7. `issues/008-remove-legacy-shim-and-duplication.md` — delete the `from_legacy` shim + duplicated paths

The detailed design (interface, dependency strategy, testing strategy) for all slices is below.

This RFC consolidates two pieces of architectural friction in the algorithms subsystem
that are best fixed together:

- **Candidate 1** — the ~80-line "raw race-card + stats → ranked field" pipeline is duplicated
  near-verbatim across two algorithm families.
- **Candidate 2** — `fit` and `predict` take *different data shapes*, forcing the gate decorator
  into a flat→decomposed→re-encode round trip and scattering the feature-transform chain across
  three call sites.

The chosen design is a **hybrid**: introduce a canonical `RaceData` value object + a single
`RaceDataBuilder` that owns the transform chain (resolves Candidate 2), consumed by a
**convention-driven template-method engine** that owns the shared data-path (resolves Candidate 1
and keeps the common win-classifier path near-zero boilerplate).

---

## Problem

### Friction 1 — the prediction data-path is written twice

`RegressorAlgorithm.predict` (`race_analytics/algorithms/regressor.py:48-127`) and
`BinaryWinClassifierAlgorithm._run_prediction` (`race_analytics/algorithms/binary_win_classifier.py:86-166`)
are two near-verbatim copies of the same pipeline:

1. merge `horse_stats` on `HorseId`; compute `DaysRested = ceil((today - LastOff)/1day)`, clamp `>10 → 10`, drop `LastOff`;
2. merge `jockey_stats` on `JockeyId`; compute `DaysSinceJockeyLastRaced` likewise, clamp, drop `LastOff`;
3. optionally merge `trainer_stats` on `TrainerId`;
4. run a chain of ~14 `encode_*`/`calculate_*` transforms from `race_analytics/features/transforms.py`;
5. `predictable = merged[["RaceId","HorseId"] + feature_cols].dropna(subset=required)`;
6. keep only races where `OriginalCount == PredictableCount` **and** `OriginalCount <= max_horses`
   (every runner survived feature-completeness, and the field is not oversized);
7. score each surviving horse and rank within race (`groupby("RaceId")[score].rank(method="dense", ascending=False)`).

The only genuine differences are the **score function** (`model.predict` → `PredictedSpeed` vs
`predict_proba(...)[:,1]` → `WinProbability`), the **output shape** (top-1 `[RaceId,HorseId]` vs the
full scored field), and a few **encode-order nuances** (the classifier calls `encode_headgear`, then
`_prepare_prediction_df`, then `_add_race_context`, then `calculate_draw_features`; the regressor calls
`calculate_horse_count` conditionally and `calculate_draw_features` last). Any change to the merge, the
`>10` clamp, or the horse-count gate must be made in both places.

### Friction 2 — `fit` and `predict` take different shapes, and the gate pays for it

`fit(train_df: pd.DataFrame)` (`base.py:96-97`) takes **one** flat, fully-enriched `race_history` frame,
but `predict(...)` / `predict_field(...)` (`base.py:100-123`) take **four** decomposed frames
`(races, horse_stats, jockey_stats, trainer_stats|None)` and re-derive every feature.

Consequences:

- **The gate is forced into a round trip.** `GatedClassifier.fit` (`gated_classifier.py:28-32`) cannot
  reuse `train_df`; it calls `decompose_race_history(race_history)` (`features/race_history.py:15-32`)
  to rebuild the four frames, then calls `inner.predict_field(...)` on them purely to score the training
  window and calibrate the confidence gate. Training data round-trips flat → decomposed → re-merged →
  re-encoded. Worse, the re-encode recomputes `DaysRested` against `datetime.today()` rather than the
  historical fold date — a latent skew/leak in calibration.
- **The transform chain runs in three places** — `evaluate._engineer_features` (~`evaluate.py:283-309`),
  `regressor.predict`, and `binary_win_classifier._run_prediction` — with subtly different orderings,
  which is a train/predict-skew surface.
- **`decompose_race_history` is not a pure inverse.** `extract_horse_stats`/`extract_jockey_stats`
  depend on columns the flat pipeline already computed (e.g. `NumberOfPriorRaces`,
  `LastRaceAvgRelFinishingPosition`), so decompose is a lossy projection that only works on an
  already-enriched frame.
- **The harness probes by reflection.** `evaluate.py` checks `hasattr(algo, "predict_field")`
  (`:457`), `hasattr(algo, "predict_field_unfiltered")` (`:461`),
  `getattr(algo, "get_confidence_gate", lambda: None)()` (`:517`), and reflects
  `type(a)(max_horses=a.max_horses)` (`:381`). There is no declared contract.

Together these make the subsystem hard to navigate: understanding one algorithm means bouncing between
the base, the family, the feature transforms, `race_history`, and the harness, and the duplication means
behavior can silently diverge between the two prediction copies.

---

## Proposed Interface

Two collaborating pieces: a **canonical data representation** (Candidate 2) and a **convention-driven
template engine** that consumes it (Candidate 1).

### A. The contract — one typed representation flows through `fit`, `predict_field`, and calibration

```python
# race_analytics/features/race_data.py
from __future__ import annotations
from dataclasses import dataclass, replace
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class RaceData:
    """Canonical, fully-engineered representation of a set of races.

    ONE flat frame, one row per horse-in-race, with EVERY feature column already
    materialised by the canonical transform chain. This is the single shape that
    flows through fit(), predict_field(), and gate calibration — there is no
    second 'decomposed' shape inside algorithm code.

    Invariants (guaranteed by RaceDataBuilder, assumed by every algorithm):
      * frame contains RaceId, HorseId, Off and all REQUIRED_PREDICTORS columns.
      * DaysRested / DaysSinceJockeyLastRaced are already clamped to <= 10.
      * The encode_*/calculate_* chain has run exactly once, in canonical order.
      * as_of is the date features were computed 'as of' (fold date for training,
        race date for serving). Recency-decay and any today-relative logic read
        THIS, never datetime.today().
      * Labels (Wins / Speed / FinishingPosition) are present iff known (training)
        and absent at serving time. Their presence is how an algorithm distinguishes
        train from predict — not a separate code path.
    """
    frame: pd.DataFrame
    as_of: pd.Timestamp
    max_horses: int = 10

    @property
    def has_labels(self) -> bool: ...
    def feature_frame(self, feature_cols: list[str]) -> pd.DataFrame: ...
    def with_columns(self, **new_cols: pd.Series) -> "RaceData": ...   # copy + add (e.g. LastProxyTSR, Rel*)
    def subset(self, mask: pd.Series) -> "RaceData": ...               # copy + filter (e.g. in-pipeline gate)


class RaceDataBuilder:
    """The single home of the merge + transform chain. Both training windows and
    serving cards enter here; nothing downstream re-encodes.

    build_training(raw, as_of) -> RaceData WITH labels.
    build_serving(card, history, as_of) -> RaceData WITHOUT labels, stats joined as-of `as_of`.

    Both run the IDENTICAL encode_*/calculate_* chain in the IDENTICAL canonical order,
    so train/predict skew is impossible by construction.
    """
    def build_training(self, raw: pd.DataFrame, as_of: pd.Timestamp, max_horses: int = 10) -> RaceData: ...
    def build_serving(self, card: pd.DataFrame, history: "RaceData | pd.DataFrame",
                       as_of: pd.Timestamp, max_horses: int = 10) -> RaceData: ...

    # Migration shim — lets algorithms move one at a time behind a green suite:
    @staticmethod
    def from_legacy(races, horse_stats, jockey_stats, trainer_stats, as_of, max_horses=10) -> RaceData: ...
```

### B. The engine — a convention-driven template that owns the shared data-path

The engine keeps the idiom the codebase already uses (`FieldPredictorBaseAlgorithm` + hooks), but the
hooks now operate on `RaceData`, and class-level **convention knobs** make the common win-classifier path
default to zero boilerplate.

```python
# race_analytics/algorithms/base.py  (deepened)
from typing import ClassVar, Protocol, runtime_checkable


@runtime_checkable
class FieldPredictor(Protocol):
    """The declared contract evaluate.py programs against — no hasattr probing."""
    max_horses: int
    def fit(self, data: RaceData) -> None: ...
    def predict_field(self, data: RaceData) -> pd.DataFrame: ...   # RaceId, HorseId, <score_col>, PredictedRank
    def predict(self, data: RaceData) -> pd.DataFrame: ...         # top-1 [RaceId, HorseId]


class FieldPredictorBaseAlgorithm(ABC):
    # ---- convention knobs (override by class assignment, not method) ----
    label_col: ClassVar[str] = "Wins"            # "Speed" for regressors
    score_col: ClassVar[str] = "WinProbability"  # "PredictedSpeed" for regressors
    return_full_field: ClassVar[bool] = True     # False -> top-1 only
    nan_tolerant_predictors: ClassVar[list[str]] = []
    extra_nan_tolerant_features: ClassVar[list[str]] = []

    def __init__(self, max_horses: int = 10):
        self.max_horses = max_horses
        self._feature_cols: list[str] = []       # selected at fit, consumed at predict

    # ---- variation-point hooks (all have identity/None defaults) ----
    def _prepare_training(self, data: RaceData) -> RaceData:  return data   # e.g. fit ProxyTSRModel, add LastProxyTSR
    def _prepare_serving(self, data: RaceData) -> RaceData:   return data   # e.g. left-join precomputed proxy TSR
    def _race_gate(self, data: RaceData) -> RaceData:         return data   # in-pipeline race filter (pre-score)
    def _sample_weight(self, frame: pd.DataFrame) -> "np.ndarray | None": return None
    @abstractmethod
    def _fit_estimator(self, X: pd.DataFrame, frame: pd.DataFrame, sample_weight) -> None: ...
    @abstractmethod
    def _score(self, X: pd.DataFrame) -> "np.ndarray": ...

    # ---- the ONE training data-path (concrete, shared) ----
    def fit(self, data: RaceData) -> None:
        data = self._prepare_training(data)
        self._feature_cols = self._select_features(data)
        train = self._dropna_required(data)
        self._fit_estimator(train.feature_frame(self._feature_cols), train.frame,
                            self._sample_weight(train.frame))

    # ---- the ONE serving data-path (concrete, shared) ----
    def predict_field(self, data: RaceData) -> pd.DataFrame:
        if not self._feature_cols:
            return _empty()
        data = self._prepare_serving(data)
        predictable = self._keep_complete_races(self._dropna_required(data))  # OriginalCount==PredictableCount<=max
        predictable = self._race_gate(predictable)
        if predictable.frame.empty:
            return _empty()
        scores = self._score(predictable.feature_frame(self._feature_cols))
        return _rank_within_race(predictable.frame, scores, self.score_col)

    def predict(self, data: RaceData) -> pd.DataFrame:        # top-1, shared
        return _top1(self.predict_field(data))

    # _select_features / _dropna_required / _keep_complete_races / _rank_within_race / _top1 / _empty
    # are concrete helpers implemented ONCE on the base.
```

### Usage

```python
# WinClassifier — only the proxy-TSR coupling is special; everything else is convention.
class WinClassifier(FieldPredictorBaseAlgorithm):
    nan_tolerant_predictors = OPTIONAL_PREDICTORS
    extra_nan_tolerant_features = RATING_COLS + PROXY_TSR_COLS

    def _prepare_training(self, data):
        self._proxy.fit(data.frame)
        self._horse_proxy = self._proxy.compute_horse_proxy_tsr(data.frame)
        return data.with_columns(LastProxyTSR=self._proxy.compute_as_of_proxy(data.frame))
    def _prepare_serving(self, data):
        return replace(data, frame=data.frame.merge(self._horse_proxy, on="HorseId", how="left"))
    def _fit_estimator(self, X, frame, sw):
        self._clf.fit(X, frame["Wins"], **({"sample_weight": sw} if sw is not None else {}))
    def _score(self, X): return self._clf.predict_proba(X)[:, 1]

# RecencyWeighted — reads RaceData.as_of, never datetime.today()
class RecencyWeightedWinClassifier(WinClassifier):
    def _prepare_training(self, data):
        data = super()._prepare_training(data)
        days_ago = (data.as_of - pd.to_datetime(data.frame["Off"])).dt.days
        return data.with_columns(_w=np.exp(-self._lambda * days_ago))
    def _sample_weight(self, frame): return frame["_w"].to_numpy()

# RatingsXGBoost — in-pipeline race gate (override one hook)
class RatingsXGBoostAlgorithm(FieldPredictorBaseAlgorithm):
    extra_nan_tolerant_features = RATING_COLS
    def _race_gate(self, data):
        complete = data.frame.groupby("RaceId")["LastRaceTopSpeedRating"].transform(lambda x: x.notna().all())
        return data.subset(complete)
    def _fit_estimator(self, X, frame, sw): self._clf.fit(X, frame["Wins"])
    def _score(self, X): return self._clf.predict_proba(X)[:, 1]

# Regressor — flip two conventions; ranking + top-1 inherited
class XGBoostAlgorithm(FieldPredictorBaseAlgorithm):
    label_col = "Speed"; score_col = "PredictedSpeed"; return_full_field = False
    nan_tolerant_predictors = OPTIONAL_PREDICTORS
    def _fit_estimator(self, X, frame, sw): self._model.fit(X, frame["Speed"])
    def _score(self, X): return self._model.predict(X)

# GatedClassifier — NO decompose_race_history; calibrate on the SAME RaceData
class GatedClassifier(FieldPredictorBaseAlgorithm):
    def fit(self, data: RaceData) -> None:
        self._inner.fit(data)
        self._calibrate(self._inner.predict_field(data))   # same object trained on — no round trip
    def predict_field(self, data: RaceData) -> pd.DataFrame:
        field = self._rules_gate.apply(self._inner.predict_field(data), data)
        return self._confidence_gate_filter(field)
```

```python
# evaluate.py — build the canonical representation ONCE per fold; no hasattr/getattr/type() probing.
builder = RaceDataBuilder()
window = builder.build_training(raw_window, as_of=pd.Timestamp(fold_date))
train_data = window.subset(pd.to_datetime(window.frame["Off"]) < fold_date)
serve_data = builder.build_serving(card=known_fold, history=train_data, as_of=pd.Timestamp(fold_date))

for algo in selected_algos:                # algo: FieldPredictor
    algo.fit(train_data)
    field = algo.predict_field(serve_data)
    preds = top1(field)
    if isinstance(algo, AbstainCapable):   # Protocol membership, not duck-typing
        unfiltered = algo.predict_field_unfiltered(serve_data)
        frontier = _roi_coverage_frontier(unfiltered, results, algo.confidence_gate)
```

### What complexity it hides

- The duplicated ~80-line data-path (merge, recency clamp, transform chain, dropna, complete-race filter,
  within-race rank) lives **once** — the merge/encode in `RaceDataBuilder`, the select/dropna/gate/rank in
  the engine template.
- The flat↔decomposed boundary disappears from algorithm code: `decompose_race_history`, `race_card`,
  and the `extract_*_stats` extractors collapse into `RaceDataBuilder.build_serving`, the only code that
  joins a raw card to per-entity stats.
- The `DaysRested`/`DaysSinceJockeyLastRaced` math + `>10` clamp moves into the builder, computed against
  `as_of`, removing the `datetime.today()` skew in gate calibration.
- The `fit→predict` state handshake (`_feature_cols` / `_fitted_predictors`) is unified into one
  `_feature_cols`; `available`/`required` re-derivation is centralized.
- The harness's reflective probing is replaced by a declared `FieldPredictor` Protocol + `isinstance`
  against an `AbstainCapable` Protocol.

---

## Dependency Strategy

**Category: In-process** (pure DataFrame transforms + injected estimators). No ports/adapters or external
mocks are required.

- **Transforms** (`features/transforms.py`) stay pure free functions. The canonical order is declared once
  as an ordered list inside `RaceDataBuilder` (borrowing the "transform chain as inspectable data" idea),
  so the encode-order nuances live in a single auditable place rather than being re-expressed per family.
- **Estimators** (`XGBClassifier` / `XGBRanker` / `Ridge` / `XGBRegressor`) remain constructor-injected
  into each algorithm and reached only through `_fit_estimator` / `_score`. The engine never imports
  xgboost/sklearn. Per-fold "fresh instance" stays trivial.
- **`decompose_race_history` / `extract_*_stats`** become internal implementation details of
  `RaceDataBuilder.build_serving`; algorithm code no longer imports `race_history` or the `*_stats`
  modules, removing the algorithm→feature-extractor coupling and the lazy imports inside `decompose`.
- **`RaceData` is frozen** with copy-on-write helpers (`with_columns`, `subset`, `replace`), preserving the
  "no I/O / no hidden mutation in algorithm code" rule. Tests construct a `FieldPredictor` with a fake
  estimator and a hand-built `RaceData`.
- **`ProxyTSRModel`, `ConfidenceGate`, `RaceRulesGate`** are unchanged collaborators; only their inputs
  change from raw frames to `RaceData`/`RaceData.frame`.

---

## Testing Strategy

**Principle: replace, don't layer.** Boundary tests on the deepened module and the builder replace tests
that asserted on intermediate variables or per-subclass plumbing.

### New boundary tests to write
- **Builder characterization (highest priority, write FIRST):** assert `RaceDataBuilder.build_serving(...).frame`
  equals today's `_run_prediction` merged/encoded intermediate on a fixed fold fixture — column-for-column,
  including the `>10` clamp and `errors="ignore"` drops. This pins behavior before any algorithm is cut over;
  given the project's leakage/ROI history, silent metric drift is expensive, so this gate is mandatory.
- **Builder train==serve parity:** `build_training` and `build_serving` produce the same feature columns in
  the same order for the same rows (proves the skew is gone).
- **`as_of` recency:** `RecencyWeightedWinClassifier` weights are computed from `RaceData.as_of`, not wall
  clock — verify by building two `RaceData` with different `as_of` and asserting different weights for the
  same rows.
- **Engine boundary:** for a `WinClassifier` over a small `RaceData` fixture — `predict_field` returns the
  full scored field with `WinProbability` + `PredictedRank`; `predict` returns top-1; the
  `OriginalCount==PredictableCount<=max_horses` filter drops the right races; `_race_gate` (RatingsXGBoost)
  drops TSR-incomplete races before scoring.
- **Gate without round trip:** `GatedClassifier.fit(data)` calibrates from `inner.predict_field(data)` and
  never calls `decompose_race_history`; calibrated threshold matches the round-trip version within tolerance
  on a fixed fixture.
- **Harness contract:** `evaluate.py` consumes algorithms via the `FieldPredictor` Protocol / `isinstance`
  with no `hasattr`/`getattr`/`type(a)(...)` probing.

### Old tests to delete or fold in
- The merge/encode assertions duplicated across `tests/algorithms/test_regressor_two_tier_dropna.py` and
  `tests/algorithms/test_binary_win_classifier.py` collapse into the single builder + engine boundary tests.
- Any test asserting on the four-frame `predict(...)` signature migrates to the `RaceData` signature (or to
  `RaceDataBuilder.from_legacy` during the staged migration).
- Per-subclass plumbing tests that only checked a hook was called become parametrized cases over
  (weighting, estimator, label) at the engine boundary.

### Test environment needs
- A small fixture: a handful of races as a flat enriched frame (or raw card + stats) sufficient to build a
  `RaceData`, with a known winner per race. Fake estimator implementing `fit`/`predict_proba`/`predict`.

---

## Implementation Recommendations

Durable guidance, independent of current file paths.

**What the module should own**
- A single canonical, fully-engineered race representation, and a single builder that is the only place the
  merge + feature-transform chain runs. Feature engineering must execute exactly once, in one canonical
  order, for both training and serving.
- The shared prediction data-path: feature selection, NaN-required dropna, the complete-race / max-field
  filter, scoring delegation, and within-race ranking.
- The fit→predict state handshake (the selected feature columns + the trained estimator).

**What it should hide**
- That a serving card is internally joined to per-entity stats (the historical "decomposed four frames" is
  an implementation detail of the builder, never a contract surface).
- The recency math and clamping, computed against an explicit `as_of` rather than wall-clock time.
- The merge/encode/rank mechanics, so an algorithm author only supplies what genuinely varies.

**What it should expose (the contract)**
- A declared `FieldPredictor` interface: `fit(data)`, `predict_field(data)` (full scored field),
  `predict(data)` (top-1) — all over the one representation. Abstention capability is a separate, declared
  capability (Protocol), not a duck-typed method probed by reflection.
- A small set of override points for the real axes of variation: training-prep, serving-prep, an in-pipeline
  race gate, sample weighting, the estimator-fit step, and the score function — with classifier-shaped
  conventions as defaults so the dominant win-classifier path is near-zero boilerplate.

**How callers migrate**
1. Land `RaceData` + `RaceDataBuilder` (with `from_legacy(...)`) and the characterization test **before**
   touching any algorithm.
2. Deepen the base into the convention-driven template; keep the four-frame `predict` working via
   `from_legacy` so algorithms migrate one at a time behind a green suite.
3. Migrate `evaluate.py` to build one `RaceData` per fold and call the `FieldPredictor` contract; delete the
   `hasattr`/`getattr`/`type(a)(...)` probing.
4. Migrate `GatedClassifier` to calibrate on the same `RaceData`; delete the `decompose_race_history` call.
5. Once every algorithm and the harness are on `RaceData`, delete the `from_legacy` shim and the duplicated
   `predict`/`_run_prediction` bodies.

**Out of scope (separate candidates):** centralizing scattered hyperparameters + replacing the index-based
`ACTIVE_ALGORITHM` registry (Candidate 4), and collapsing the thin weighting/objective subclasses into
composable strategy objects (Candidate 5). This RFC deliberately keeps those untouched to bound the blast
radius of the contract change.
