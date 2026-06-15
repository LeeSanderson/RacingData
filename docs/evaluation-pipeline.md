# Evaluation & Prediction Pipeline

How algorithms are evaluated and how production predictions are made. For the
current active algorithm and the latest measured numbers, see `evaluations.md`
(the live source of truth) — this doc covers the *methodology*, which is stable.

## Two scripts

| Script | Role | Reads | Writes |
|---|---|---|---|
| `race_analytics/scripts/evaluate.py` | Offline algorithm comparison (standalone) | raw `Results_YYYYMM.csv`, engineers features in-memory | nothing, unless `--save-results`/`--results-file` (then a per-fold CSV) |
| `race_analytics/scripts/predict.py` | Production — picks for today's cards | pre-computed `Race_Features.csv`, `Horse_Stats.csv`, `Jockey_Stats.csv`, `Trainer_Stats.csv`, `TodaysRaceCards.csv` | `TodaysPredictions.csv` (consumed by the `validate` CLI step) |

`evaluate.py` is deliberately self-contained: it re-engineers features from raw
results per fold rather than reading `Race_Features.csv`, so a fold never sees
data from after its cut-off date. `predict.py` trusts the pre-built feature CSVs
produced by `build_features.py`.

## Walk-forward methodology

- **One fold per day.** Each fold trains on the 7 most-recent months *strictly
  before* the fold date and predicts on the fold date. Models are re-fit every
  fold on fresh instances (prevents XGBoost's C++ memory pool accumulating).
- **Defaults:** 14 daily folds, 7-month training window. Override with
  `--folds N` and `--training-months M`.
- **No leakage:** because each fold engineers features only from results before
  its date, and the test rows are the fold date itself, future information
  cannot reach the model. See `docs/data-pitfalls.md` for the subtler traps.

## Algorithm registry & interface

The registry lives in `race_analytics/algorithms/__init__.py`: `ALGORITHMS` is a
list of instantiated algorithms; `ACTIVE_ALGORITHM` is the one `predict.py` uses
in production.

Class hierarchy (`race_analytics/algorithms/base.py`):

- `BaseAlgorithm` — abstract `fit(train_df)` and
  `predict(races, horse_stats, jockey_stats, trainer_stats=None) -> {RaceId, HorseId}`.
- `RegressorAlgorithm` — sklearn-style models; subclasses implement `_create_model()`
  (e.g. `RidgeRegressionAlgorithm`, `XGBoostAlgorithm`).
- `FieldPredictorBaseAlgorithm` — adds `predict_field()` (a row per horse with
  `WinProbability`/`PredictedRank`); provides `predict()` by taking the rank-1 row
  per race. The win-classifier family extends this.
- `GatedClassifier` — a decorator that wraps any field predictor with a **two-gate
  abstain layer**: a confidence gate (threshold from a training-window coverage
  quantile) plus a short list of hard-race rules. Gated algorithms decline to bet
  on low-confidence races.

## Filters applied before any algorithm sees data

1. `KnownHorseAndJockey == True` — both the horse and jockey must have prior history.
2. Every horse in a race must have non-null `REQUIRED_PREDICTORS`; `OPTIONAL_PREDICTORS`
   (e.g. `Last3*`) are tolerated via each algorithm's `nan_tolerant_predictors`.
   A race with any null required predictor for any runner is silently excluded.
3. Field size ≤ `max_horses` (a per-algorithm constructor parameter, default 10).

## Metrics

Definitions live in `race_analytics/utils/scoring.py` and apply only to
`ResultStatus == "CompletedRace"` rows:

- **accuracy** (primary) — fraction of top picks that finish 1st.
- **roi** — net £ on flat £1 stakes: `Σ DecimalOdds of winning picks − number of bets`.
  ROI is informational, not the optimisation target. Note `DecimalOdds` come from
  `Results_*.csv` (retrospective) — odds are *not* available at prediction time,
  so ROI is a measurement construct only (see `docs/data-pitfalls.md`).
- **coverage** — fraction of predictable races a gated algorithm actually bets on.
- **Baseline** — market favourite (lowest decimal odds in each race), printed alongside.
- For gated algorithms, `evaluate.py` prints a **ROI-vs-coverage frontier** so you
  can see the trade-off between betting more races and ROI.

## Timing & AFK guidance

Per-fold wall time is dominated by **feature engineering**, not model fitting. The
stats calculators (`CalculateHorsesStats`, `CalculateJockeyStats`,
`CalculateTrainerStats`, `CalculateRacesWithKnownHorsesAndJockeys`) iterate
day-by-day over the training window — O(days × records/day).

- Feature engineering: ~5-7 min/fold (~88k rows over a 7-month window)
- Win-classifier family fit (e.g. `GatedRecencyWeightedWinClassifier`): ~17-35 s
  (proxy computation dominates); cheap regressors like XGBoost fit in <1 s
- **Total: ~6-8 min/fold**

Estimate AFK runs as `folds × 6-8 min × num_algorithms`:

- 14 folds (default): ~1.5-2 hours
- 180-fold comparison across 2 algorithms: ~36-48 hours — run as an overnight task

`race_analytics/scripts/feature_screen.py` uses a single bulk fit to screen many
candidate features without paying the per-fold stats cost 180 times.

## Running it

```powershell
# Build feature CSVs (last 7 months) — run before predict.py
python -m race_analytics.scripts.build_features --data Data

# Production predictions for today's cards
python -m race_analytics.scripts.predict --data Data

# Offline evaluation (default 14 folds); add --save-results to persist a CSV
python -m race_analytics.scripts.evaluate --folds 180 --training-months 7 --save-results

# Resume a crashed long run from fold N
python -m race_analytics.scripts.evaluate --folds 180 --fold-offset N
```
