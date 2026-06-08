# PRD: Accuracy and ROI Improvements — Round 2

## Problem Statement

The current active algorithm (`AbstainWrapperAlgorithm`) achieves 0.299 accuracy and −£62 ROI
over a 180-fold walk-forward evaluation. It wraps a ProxyTSR XGBoost binary classifier with a
confidence gate (top_prob @ 70% coverage) and a hard race-rules filter (no sprints, no Class 6).

Several improvement directions have been validated or identified through analysis:

- The `HeadGear` column in the raw data (first-time blinkers, cheekpieces, tongue-tie, etc.) is
  entirely absent from the model despite being a well-known form indicator.
- The binary win/lose training target discards relative finishing position — a horse that finishes
  2nd of 10 is treated identically to one that finishes 10th of 10.
- A single XGBoost model trained on flat and jump races together may be suboptimal for both
  disciplines, which have fundamentally different predictive signals.
- Training samples from 7 months ago carry the same weight as last week's races, even though
  recent form is more predictive.
- A 30-fold validation experiment confirmed that the gap confidence metric improves accuracy
  (+3.1pp) but worsens ROI — establishing that **ROI, not accuracy, is the primary objective**
  and that these two metrics can diverge significantly.
- `WinProbability` is now written to `TodaysPredictions.csv` but is not yet carried through into
  the `PredictionScores_YYYYMM.csv` history, preventing future Kelly-criterion staking analysis.

## Solution

Implement five new algorithm variants and one set of base feature improvements, evaluate all
variants in a single 180-fold walk-forward run, and adopt any variant that improves ROI over the
current −£62 baseline with a stable early-vs-late gain.

The improvements are independent: HeadGear features benefit all algorithms immediately and should
be implemented first. The five algorithm variants are then implemented and evaluated together.

## User Stories

1. As a modeller, I want first-time headgear changes encoded as features, so that the model can
   learn that a horse wearing blinkers for the first time often runs to a different level.
2. As a modeller, I want binary flags for each headgear type (blinkers, cheekpieces, tongue-tie,
   hood, visor), so that the model distinguishes between types of headgear rather than treating
   all headgear as equivalent.
3. As a modeller, I want a `HeadGearChanged` boolean feature computed from the horse-stats join,
   so that any headgear change (not just first-time use) is signalled to the model.
4. As a modeller, I want HeadGear features computed as as-of-date stats (using only prior races
   for each horse), so that no future race data leaks into training rows.
5. As a modeller, I want `IsFirstTimeHeadgear` and all headgear flags added to
   `OPTIONAL_PREDICTORS`, so that all algorithms that inherit from `BinaryWinClassifierAlgorithm`
   benefit automatically.
6. As a modeller, I want a `WeightedPositionProxyTSRAlgorithm` that weights training samples by
   `1/FinishingPosition`, so that finishing position carries a richer gradient signal without
   architectural change.
7. As a modeller, I want a `LTRProxyTSRAlgorithm` that uses XGBoost's `rank:pairwise` objective
   on finishing position labels within each race, so that the model directly optimises for ranking
   rather than binary win classification.
8. As a modeller, I want `LTRProxyTSRAlgorithm` to use the score gap (top_score − second_score)
   as its confidence metric, so that the abstain layer is calibrated appropriately for a
   ranking model that produces scores rather than probabilities.
9. As a modeller, I want a `SplitRaceTypeAlgorithm` that trains separate ProxyTSRXGBoost models
   for flat and jump races, so that each discipline uses only relevant training signal.
10. As a modeller, I want `SplitRaceTypeAlgorithm` to fall back to a combined model when a race
    type has insufficient training data, so that predictions are never silently dropped.
11. As a modeller, I want a `RecencyWeightedProxyTSRAlgorithm` that applies exponential decay
    weighting to training samples, so that recent form is weighted more heavily than stale form
    from 6–7 months ago.
12. As a modeller, I want each new algorithm variant wrapped in `AbstainWrapperAlgorithm` (or an
    appropriate abstain layer) for evaluation, so that comparisons are fair against the current
    active algorithm.
13. As a modeller, I want all five variants included in a single 180-fold walk-forward eval run
    alongside the current `AbstainWrapperAlgorithm` baseline, so that results are directly
    comparable on the same folds.
14. As a modeller, I want the eval to report ROI as the primary metric and accuracy/coverage as
    secondary, so that adoption decisions are not misled by accuracy gains that come at the cost
    of ROI.
15. As a modeller, I want the early-vs-late stability split reported for every new variant, so
    that I can confirm any ROI improvement is not confined to a single time period.
16. As a punter using `PredictionScores_YYYYMM.csv`, I want `WinProbability` carried through from
    `TodaysPredictions.csv` into the scored history, so that I can apply Kelly-criterion stake
    sizing once SP odds are available after each race.
17. As a punter, I want `WinProbability` visible in the scored history for every historical pick,
    so that I can retrospectively analyse whether high-confidence picks outperform low-confidence
    ones.

## Implementation Decisions

### HeadGear features

- Add `encode_headgear` transform function in `race_analytics/features/transforms.py`. Inputs:
  the raw `HeadGear` column. Outputs: `IsFirstTimeHeadgear` (any `*1` suffix), `HasBlinkers`,
  `HasCheekpieces`, `HasTongueTie`, `HasHood`, `HasVisor` (binary flags from the headgear code),
  and `HeadGearChanged` (current headgear ≠ last-race headgear from horse stats join).
- Null `HeadGear` encodes as "no headgear" — all flags false, not NaN.
- `HeadGearChanged` requires a `LastRaceHeadGear` column added to `CalculateHorsesStats` in
  `race_analytics/features/horse_stats.py`, recording the raw headgear code from the horse's
  most recent prior race. This must be computed from the horse's historical slice, not the
  current race row.
- All new columns added to `OPTIONAL_PREDICTORS` in `race_analytics/algorithms/base.py`.
- `encode_headgear` called in `BinaryWinClassifierAlgorithm._run_prediction` (alongside the
  existing `encode_surfaces`, `encode_going`, etc. calls) and in `_engineer_features` in
  `evaluate.py`.
- Validate with `feature_screen.py` before proceeding to algorithm variants — confirm no
  odds-related leakage and that at least some headgear flags have non-zero XGBoost importance.

### WeightedPositionProxyTSRAlgorithm

- New class in `race_analytics/algorithms/proxy_tsr_xgboost.py`, inheriting from
  `ProxyTSRXGBoostAlgorithm`.
- Override `fit()`: compute `sample_weight = 1 / FinishingPosition` for each training row
  (winner = 1.0, 2nd = 0.5, …). Pass to `_classifier.fit(X, y, sample_weight=weights)`.
- Expose a wrapped variant `AbstainWeightedPositionAlgorithm` (inherits
  `AbstainWrapperAlgorithm`, sets base to `WeightedPositionProxyTSRAlgorithm`).
- Register both in `__init__.py` `ALGORITHMS` list.

### LTRProxyTSRAlgorithm

- New class in a new file `race_analytics/algorithms/ltr_proxy_tsr.py`, inheriting from
  `BinaryWinClassifierAlgorithm` but replacing the classifier with `XGBRanker`.
- `fit()` override: sort training data by `RaceId`, compute group sizes (horses per race), set
  labels = `HorseCount − FinishingPosition + 1` (winner gets highest label). Call
  `_ranker.fit(X, labels, group=group_sizes)`.
- `_run_prediction()` override: call `_ranker.predict(X)` (returns scores, not probabilities).
  Store as `WinProbability` column for interface compatibility (score, not a calibrated
  probability — downstream code treats it as a ranking score). Rank within race by score
  descending.
- Confidence gate: a dedicated `AbstainWrapperLTRAlgorithm` class using `metric="gap"` (score
  gap between 1st- and 2nd-ranked horse) since LTR scores are not probabilities and `top_prob`
  is not meaningful.
- Register `LTRProxyTSRAlgorithm` and `AbstainWrapperLTRAlgorithm` in `ALGORITHMS`.

### SplitRaceTypeAlgorithm

- New class in `race_analytics/algorithms/split_race_type.py`, inheriting from `BaseAlgorithm`.
- Holds two `ProxyTSRXGBoostAlgorithm` instances: `_flat_model` and `_jumps_model`.
- `fit()`: split training data by `RaceType_Flat == 1` vs hurdle/chase; fit each sub-model if
  it has ≥ 100 training races, otherwise mark as unavailable and fall back to a combined model
  fitted on all data.
- `predict()` / `predict_field()`: route each race to the appropriate sub-model; if a race type
  is unavailable, use the fallback. Merge outputs before returning.
- Expose `AbstainWrapperSplitAlgorithm` wrapping `SplitRaceTypeAlgorithm`.
- Register both in `ALGORITHMS`.

### RecencyWeightedProxyTSRAlgorithm

- New class in `race_analytics/algorithms/proxy_tsr_xgboost.py`, inheriting from
  `ProxyTSRXGBoostAlgorithm`.
- Constructor accepts `decay_lambda: float = 0.01` (half-weight at ~70 days).
- `fit()` override: compute `days_ago = fold_date − race_date` for each training row; set
  `sample_weight = exp(−decay_lambda × days_ago)`. Pass to `_classifier.fit()`.
- The fold date is inferred as `train_df["Off"].max().date() + timedelta(days=1)`.
- Expose `AbstainRecencyWeightedAlgorithm` wrapping this class.
- Register both in `ALGORITHMS`.

### PredictionScores WinProbability

- The .NET tool (C# `RaceDataDownloader`) that generates `PredictionScores_YYYYMM.csv` reads
  `TodaysPredictions.csv` and merges it with race results. It must be updated to carry the
  `WinProbability` column through to the output CSV.
- If `WinProbability` is absent from `TodaysPredictions.csv` (legacy rows), write `null`/empty
  for that column rather than failing.
- Schema change: `PredictionScores_YYYYMM.csv` gains a `WinProbability` column (nullable float).

### Evaluation run

- All wrapped variants (`AbstainWeightedPositionAlgorithm`, `AbstainWrapperLTRAlgorithm`,
  `AbstainWrapperSplitAlgorithm`, `AbstainRecencyWeightedAlgorithm`) run alongside the current
  `AbstainWrapperAlgorithm` in a single 180-fold run.
- `AbstainWrapperGapAlgorithm` included for completeness (already registered).
- Command: `python -m race_analytics.scripts.evaluate --folds 180 --training-months 7
  --algorithms "AbstainWrapperAlgorithm,AbstainWrapperGapAlgorithm,AbstainWeightedPositionAlgorithm,AbstainWrapperLTRAlgorithm,AbstainWrapperSplitAlgorithm,AbstainRecencyWeightedAlgorithm" --save-results`
- Acceptance bar: any variant with ROI > −62 (improvement over current baseline) and stable
  early-vs-late gain is a candidate for adoption. Update `ACTIVE_ALGORITHM` and `evaluations.md`
  for the winner.

## Testing Decisions

- `encode_headgear` is a pure function: write pytest tests in `tests/features/` asserting correct
  flag values for known headgear codes (`"b1"` → `HasBlinkers=True, IsFirstTimeHeadgear=True`),
  null input (all False), and multi-code combinations (`"tp1"` → `HasTongueTie=True,
  HasCheekpieces=True, IsFirstTimeHeadgear=True`).
- `CalculateHorsesStats` `LastRaceHeadGear` computation: add a test in
  `tests/features/test_horse_stats.py` verifying that `LastRaceHeadGear` reflects the horse's
  most recent prior race, not the current race row.
- `WeightedPositionProxyTSRAlgorithm`: no dedicated unit test — the sample weight calculation is
  trivial; correctness verified via the comparative eval run.
- `LTRProxyTSRAlgorithm`: write a pytest smoke test asserting that `fit()` + `predict_field()`
  completes without error on a small synthetic DataFrame and returns the expected columns
  (`RaceId`, `HorseId`, `WinProbability`, `PredictedRank`).
- `SplitRaceTypeAlgorithm`: write a pytest test asserting correct routing (flat races go to
  flat model, jumps races go to jumps model) and that fallback triggers when a race type has
  fewer than 100 training rows.
- `RecencyWeightedProxyTSRAlgorithm`: no dedicated unit test — weight formula is simple; verified
  via eval.
- `feature_screen.py` run after HeadGear implementation: confirms headgear flags have non-zero
  importance and no odds-derived features are present.
- C# `PredictionScores` change: add a test in the existing xUnit suite asserting that when
  `TodaysPredictions.csv` contains a `WinProbability` column, the scored output carries it
  through; and when the column is absent, the output writes empty/null without throwing.

### Algorithm composability refactor

- Replace the MRO-based multiple-inheritance pattern with a true decorator `GatedClassifier(inner: BaseAlgorithm)`.
- `GatedClassifier.fit(race_history)` calls `inner.fit(race_history)`, decomposes the history via
  `decompose_race_history()` (new utility in `race_analytics/features/race_history.py`), then calls
  `inner.predict_field(races, horse_stats, jockey_stats, trainer_stats)` for confidence-gate
  calibration. No shared private state between wrapper and inner.
- `decompose_race_history()` composes `race_card()` (moved from `evaluate.py`) with the existing
  `extract_horse_stats/jockey_stats/trainer_stats` functions.
- Rename all algorithms to descriptive-intent names — see rename map in
  `issues/020-algorithm-composability-implementation.md`.
- One file per substantive algorithm; thin one-liner named subclasses kept in `__init__.py` for
  the registry (so results CSVs and eval pipeline need no schema changes).
- `SplitDisciplineWinClassifier` accepts `inner_class=WinClassifier` constructor parameter,
  enabling cross-axis combinations (e.g. split + recency-weighted) without new classes.
- `_prepare_training_df()` and `_prepare_prediction_df()` hooks retained inside `WinClassifier`
  hierarchy for proxy TSR injection — invisible to `GatedClassifier`.
- Eval CSVs and `evaluations.md` updated to use new algorithm names.
- See `issues/020-algorithm-composability-implementation.md` for full implementation plan.

## Out of Scope

- Course-specific features: horse-course win rates are too sparse (88.9% of horse-course pairs
  appear only once). Course groupings (handedness, track shape) are not in the raw data.
- Trainer-jockey combination stats: 52% of combinations appear only once across 6 months.
- Kelly-criterion staking in production: odds are unavailable at prediction time (SP only).
  `WinProbability` is added to history to enable future offline Kelly analysis only.
- Probability calibration (Platt scaling / isotonic regression) of XGBoost outputs: the 30-fold
  validation showed calibration bias is small (72.9% actual vs 70% target coverage).
- Increasing the `max_horses` cap above 10: prior analysis confirmed that larger fields are
  materially harder to predict.
- Confidence gate metric change (gap vs top_prob) as the active gate: the 30-fold validation
  confirmed gap improves accuracy but worsens ROI. `AbstainWrapperGapAlgorithm` remains in the
  registry for monitoring but is not adopted as active.

## Further Notes

- **ROI vs accuracy divergence**: the 30-fold gap-metric experiment confirmed these objectives
  can diverge significantly. A metric that selects more "certain" winners tends to select
  shorter-priced horses that the market has already found — higher accuracy, lower value, worse
  ROI. All future algorithm adoption decisions must use ROI as the primary gate.
- **30-fold late-period result**: `AbstainWrapperAlgorithm` was +£11.10 ROI in the most recent
  15 folds of the validation run, suggesting the current model may be in a positive patch. The
  180-fold run will give a more stable picture.
- **Eval timing**: 180 folds × ~25s/fold × 6 algorithms ≈ 75 hours. Run overnight or across
  multiple sessions using `--fold-offset` for crash recovery. Consider running HeadGear-only
  first (2 algorithms, ~10 hours) to confirm the feature adds value before the full run.
- **WinProbability naming in LTR**: `LTRProxyTSRAlgorithm` reuses the `WinProbability` column
  name for ranking scores (not true probabilities). Downstream code and CSV consumers should
  treat this column as a relative score, not an absolute probability, when the active algorithm
  is LTR-based.
