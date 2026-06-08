## Type

AFK

## Parent PRD

`issues/prd.md`

## Context

Issue 019 (HITL design review) resolved the composability strategy. The current algorithm hierarchy
uses multiple-inheritance MRO chains that couple the abstain wrapper tightly to each base algorithm.
This issue implements the agreed decorator/wrapper pattern and naming overhaul.

## Goals

1. Replace MRO-based composition with a true decorator `GatedClassifier(inner: BaseAlgorithm)`.
2. Rename all algorithms to descriptive-intent names.
3. One substantive file per algorithm; thin registry subclasses in `__init__.py`.
4. Extract `decompose_race_history()` utility so the wrapper can call `predict_field()` for
   calibration without double-merging stats.
5. Parameterise `SplitDisciplineWinClassifier` so cross-axis combos require no new class.
6. Update evaluation CSVs and `evaluations.md` to use new names.

## Algorithm rename map

| Old name | New name |
|---|---|
| `ProxyTSRXGBoostAlgorithm` | `WinClassifier` |
| `WeightedPositionProxyTSRAlgorithm` | `PositionWeightedWinClassifier` |
| `RecencyWeightedProxyTSRAlgorithm` | `RecencyWeightedWinClassifier` |
| `TunedProxyTSRXGBoostAlgorithm` | `TunedWinClassifier` |
| `SplitRaceTypeAlgorithm` | `SplitDisciplineWinClassifier` |
| `LTRProxyTSRAlgorithm` | `RankingClassifier` |
| `AbstainWrapperAlgorithm` (generic wrapper) | `GatedClassifier` |
| `AbstainWrapperAlgorithm` (registry entry) | `GatedWinClassifier` |
| `AbstainWrapperGapAlgorithm` | `GatedGapWinClassifier` |
| `AbstainWeightedPositionAlgorithm` | `GatedPositionWeightedWinClassifier` |
| `AbstainRecencyWeightedAlgorithm` | `GatedRecencyWeightedWinClassifier` |
| `AbstainWrapperSplitAlgorithm` | `GatedSplitDisciplineWinClassifier` |
| `AbstainWrapperLTRAlgorithm` | `GatedRankingClassifier` |

## Implementation plan

### 1. `decompose_race_history()` utility

Add to `race_analytics/features/race_history.py` (new file):

```python
def race_card(race_history: pd.DataFrame) -> pd.DataFrame:
    """Strip an enriched race_history DataFrame to raw race-card columns only."""
    cols = ["RaceId", "HorseId", "JockeyId", "TrainerId", "Surface", "Going",
            "RaceType", "DistanceInMeters", "WeightInPounds", "Class", "Age",
            "StallNumber", "Pattern", "RatingBand", "AgeBand", "SexRestriction", "HeadGear"]
    return race_history[[c for c in cols if c in race_history.columns]].copy()

def decompose_race_history(race_history: pd.DataFrame):
    """Decompose an enriched race_history into (races, horse_stats, jockey_stats, trainer_stats)."""
    from race_analytics.features.horse_stats import extract_horse_stats
    from race_analytics.features.jockey_stats import extract_jockey_stats
    from race_analytics.features.trainer_stats import extract_trainer_stats
    return (
        race_card(race_history),
        extract_horse_stats(race_history),
        extract_jockey_stats(race_history),
        extract_trainer_stats(race_history),
    )
```

Update `evaluate.py` to use `decompose_race_history()` instead of its current manual equivalent
(`_race_card()` + separate `extract_*` calls). Remove `_race_card()` from `evaluate.py`.

### 2. `GatedClassifier` — true decorator

New file `race_analytics/algorithms/gated_classifier.py`:

```python
class GatedClassifier(BaseAlgorithm):
    def __init__(self, inner: BaseAlgorithm, metric: str = "top_prob", coverage: float = 0.7):
        super().__init__(inner.max_horses)
        self._inner = inner
        self._confidence_gate = ConfidenceGate(metric)
        self._rules_gate = RaceRulesGate()
        self._coverage = coverage

    def fit(self, race_history: pd.DataFrame) -> None:
        self._inner.fit(race_history)
        races, horse_stats, jockey_stats, trainer_stats = decompose_race_history(race_history)
        training_field = self._inner.predict_field(races, horse_stats, jockey_stats, trainer_stats)
        self._calibrate(training_field)

    def _calibrate(self, training_field: pd.DataFrame) -> None:
        gate = self._confidence_gate
        race_scores = training_field.groupby("RaceId")["WinProbability"].apply(gate.score).tolist()
        gate.calibrate(race_scores, self._coverage)

    def predict_field(self, races, horse_stats, jockey_stats, trainer_stats=None) -> pd.DataFrame:
        field = self._inner.predict_field(races, horse_stats, jockey_stats, trainer_stats)
        field = self._apply_rules_gate(field, races)
        return self._apply_confidence_gate(field)

    def predict(self, races, horse_stats, jockey_stats, trainer_stats=None) -> pd.DataFrame:
        field = self.predict_field(races, horse_stats, jockey_stats, trainer_stats)
        if field.empty or "PredictedRank" not in field.columns:
            return pd.DataFrame(columns=["RaceId", "HorseId"])
        return (
            field[field["PredictedRank"] == 1][["RaceId", "HorseId"]]
            .drop_duplicates(subset=["RaceId"])
            .reset_index(drop=True)
        )

    def predict_field_unfiltered(self, races, horse_stats, jockey_stats, trainer_stats=None):
        """Field with rules gate only — no confidence gate. For ROI-vs-coverage frontier."""
        field = self._inner.predict_field(races, horse_stats, jockey_stats, trainer_stats)
        return self._apply_rules_gate(field, races)

    def get_confidence_gate(self) -> ConfidenceGate:
        return self._confidence_gate
```

### 3. New algorithm files

Create one file per substantive algorithm, renaming as per the map above:

- `race_analytics/algorithms/win_classifier.py` — `WinClassifier`
  (content of current `ProxyTSRXGBoostAlgorithm`; keep `_prepare_training_df` and
  `_prepare_prediction_df` hooks for proxy TSR injection)
- `race_analytics/algorithms/position_weighted_win_classifier.py` — `PositionWeightedWinClassifier`
- `race_analytics/algorithms/recency_weighted_win_classifier.py` — `RecencyWeightedWinClassifier`
- `race_analytics/algorithms/tuned_win_classifier.py` — `TunedWinClassifier`
- `race_analytics/algorithms/split_discipline_win_classifier.py` — `SplitDisciplineWinClassifier`
- `race_analytics/algorithms/ranking_classifier.py` — `RankingClassifier`

Delete old files once content is migrated:
- `proxy_tsr_xgboost.py` (replaced by four new files)
- `abstain_wrapper.py` (replaced by `gated_classifier.py`)
- `split_race_type.py` (replaced by `split_discipline_win_classifier.py`)
- `ltr_proxy_tsr.py` (replaced by `ranking_classifier.py`)

### 4. `SplitDisciplineWinClassifier` parameterisation

`split_discipline_win_classifier.py` constructor:

```python
def __init__(self, inner_class=WinClassifier, max_horses: int = 10):
    super().__init__(max_horses=max_horses)
    self._flat_model = inner_class(max_horses=max_horses)
    self._jumps_model = inner_class(max_horses=max_horses)
    self._fallback_model = inner_class(max_horses=max_horses)
```

### 5. `__init__.py` — thin registry subclasses

```python
class GatedWinClassifier(GatedClassifier):
    def __init__(self, **kwargs): super().__init__(WinClassifier(**kwargs))

class GatedGapWinClassifier(GatedClassifier):
    def __init__(self, **kwargs): super().__init__(WinClassifier(**kwargs), metric="gap", coverage=0.5)

class GatedPositionWeightedWinClassifier(GatedClassifier):
    def __init__(self, **kwargs): super().__init__(PositionWeightedWinClassifier(**kwargs))

class GatedRecencyWeightedWinClassifier(GatedClassifier):
    def __init__(self, **kwargs): super().__init__(RecencyWeightedWinClassifier(**kwargs))

class GatedSplitDisciplineWinClassifier(GatedClassifier):
    def __init__(self, **kwargs): super().__init__(SplitDisciplineWinClassifier(**kwargs))

class GatedRankingClassifier(GatedClassifier):
    def __init__(self, **kwargs): super().__init__(RankingClassifier(**kwargs), metric="gap")
```

Update `ALGORITHMS` list and `ACTIVE_ALGORITHM` to use new names.

### 6. Update evaluation artefacts

- **Eval CSVs**: find-replace old algorithm names with new names in
  `evaluation_results_20260606.csv`, `evaluation_comparison_20260602.csv`,
  `evaluation_results_20260531.csv` (use the rename map above).
- **`evaluations.md`**: update all algorithm name references, file path references
  (`abstain_wrapper.py` → `gated_classifier.py`, `proxy_tsr_xgboost.py` → `win_classifier.py`,
  etc.), and the active algorithm code block.

### 7. Update other references

Grep for old algorithm class names across the codebase (tests, scripts, any markdown) and update:
- `tests/` — update imports and class names in all algorithm tests
- `predict.py` — update any ACTIVE_ALGORITHM references if hardcoded
- Comments referencing old names

## Testing

- All existing algorithm tests must pass with new names — update imports only, no logic changes.
- Add a test for `GatedClassifier` in `tests/algorithms/test_gated_classifier.py`:
  - `fit()` + `predict_field()` on a small synthetic DataFrame returns expected columns
  - `predict()` returns one row per race (rank 1 only)
  - `predict_field_unfiltered()` returns more rows than `predict_field()` (confidence gate bypassed)
- Add a test for `decompose_race_history()` in `tests/features/test_race_history.py`:
  - `race_card()` returns only the 17 raw columns
  - `decompose_race_history()` returns four DataFrames with expected shapes
- `SplitDisciplineWinClassifier` existing routing test: update class name, verify
  `inner_class` param works with `RecencyWeightedWinClassifier`.

## Acceptance criteria

- [ ] All algorithm files renamed and old files deleted.
- [ ] `GatedClassifier` is a true decorator — no inheritance from inner algorithm, no access to inner
      private attributes.
- [ ] `decompose_race_history()` utility in `race_analytics/features/race_history.py`; `evaluate.py`
      uses it.
- [ ] `SplitDisciplineWinClassifier` accepts `inner_class` parameter.
- [ ] Thin named subclasses in `__init__.py`; substantive algorithm logic in individual files.
- [ ] All tests pass (`pytest tests/`).
- [ ] Eval CSVs and `evaluations.md` updated with new names.
- [ ] `predict.py` smoke-runs without error after rename.
