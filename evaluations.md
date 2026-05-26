# Algorithm Evaluation Findings

## Baseline Results (14 folds, 194 races)

| Algorithm | Accuracy | ROI |
|---|---|---|
| RidgeRegressionAlgorithm | 0.222 | -14.82 |
| XGBoostAlgorithm | 0.227 | -27.45 |
| Market Favourite baseline | 0.347 | -16.23 |

Both algorithms underperform the market favourite on accuracy and ROI.

---

## Root Cause Analysis

### 1. Wrong target variable

Both algorithms predict absolute **Speed** (metres per second) and pick the horse with the highest predicted speed per race. Speed is heavily determined by race conditions, not horse quality:

- `OfficialRating` correlation with Speed = **-0.62** — higher-rated horses run *slower* in absolute terms because they race at longer, more competitive distances on softer ground.
- XGBoost feature importance: `RaceType_Other` = **94%** of importance budget. The model learned "what speed does this race type produce?" not "which horse will win?".

### 2. Missing key predictors

The `PREDICTORS` list (37 features) omits the strongest win predictors available in the data:

| Feature | Correlation with Wins | Coverage |
|---|---|---|
| `RacingPostRating` (relative to field) | **+0.388** | 52% |
| `TopSpeedRating` (relative to field) | **+0.381** | 49% |
| `RacingPostRating` (absolute) | +0.266 | 52% |
| `TopSpeedRating` (absolute) | +0.218 | 49% |
| `OfficialRating` (relative to field) | +0.084 | 69% |
| `LastRaceSpeed` (current best feature) | -0.038 | 67% |

`LastRaceSpeed` — relied upon heavily by both existing algorithms — is 10× weaker than `RacingPostRating` at predicting winners.

---

## RatingsXGBoostAlgorithm

### Design changes

- **Target**: `Wins` (binary 0/1) instead of Speed
- **Model**: `XGBClassifier` (win probability) instead of `XGBRegressor`
- **New features**: `OfficialRating`, `RacingPostRating`, `TopSpeedRating` (absolute + relative to field average)
- **HorseCount** added as feature
- **NaN handling**: ratings may be NaN; only `PREDICTORS` are required non-null; XGBoost handles missing values natively

### 60-fold results (950 races)

| Algorithm | Accuracy | ROI | vs Favourite |
|---|---|---|---|
| RidgeRegressionAlgorithm | 0.242 | +64.73 | +98.93 |
| XGBoostAlgorithm | 0.235 | -57.76 | -23.56 |
| **RatingsXGBoostAlgorithm** | **0.305** | **+253.64** | **+287.83** |
| Market Favourite baseline | 0.359 | -34.20 | — |

RatingsXGBoost achieves the best accuracy of the ML algorithms and the only strongly positive ROI, averaging **+26.7p return per £1 bet** across 950 races.

---

## TopSpeedRating as Key Driver

### High-accuracy vs low-accuracy fold analysis

| Group | Avg accuracy | Avg ROI | Avg field size | TSR coverage | Winner avg odds |
|---|---|---|---|---|---|
| High-accuracy folds (7) | 0.658 | +46.55 | 6.7 | 71% | 5.97 |
| Low-accuracy folds (7) | 0.167 | -8.00 | 7.3 | 0% | 2.68 |

**Field size is not the driver**. `TopSpeedRating` (TSR) coverage is the key differentiator:
- Days with TSR ≥95% for all horses: consistently 0.667–0.875 accuracy, strongly positive ROI
- Days with 0% TSR: mostly 0.077–0.211 accuracy, negative ROI

When TSR is absent, the algorithm degenerates to a low-quality favourite-picker (winner odds 2.68 ≈ favourite baseline 2.65). When TSR is present, it identifies genuine value: longer-priced winners the market underestimates.

**Why TSR is inconsistent**: TopSpeedRating is a Racing Post proprietary calculation, only available for horses with sufficient race history. New horses and lightly-raced horses have no TSR.

### Race availability under TSR-complete filter (60 folds)

| Filter | Avg races/day | Total | % of races |
|---|---|---|---|
| KnownHorseAndJockey (current) | 15.8 | 934 | 100% |
| + TopSpeedRating complete (all horses) | 1.6 | 93 | 10% |
| + OfficialRating complete (all horses) | 13.7 | 806 | 86% |

TSR-complete races: available only **19% of days**, with 81% of days having zero qualifying races.

---

## TSR-Gated Strategy

Adding `require_tsr=True` (default) to `RatingsXGBoostAlgorithm` filters predictions to races where **all horses have a TopSpeedRating**. This reduces volume to ~1.6 races/day but concentrates predictions on the algorithm's high-confidence operating conditions.

### 60-fold results with TSR gating (934 races total, 93 gated)

| Algorithm | Accuracy | ROI | Races | ROI/race |
|---|---|---|---|---|
| RidgeRegressionAlgorithm | 0.242 | +67.63 | 934 | +0.07 |
| XGBoostAlgorithm | 0.231 | -68.36 | 934 | -0.07 |
| **RatingsXGBoostAlgorithm (TSR-gated)** | **0.602** | **+313.12** | **93** | **+3.37** |
| RatingsXGBoostUngatedAlgorithm | 0.304 | +254.51 | 934 | +0.27 |
| Market Favourite (on gated races) | 0.290 | -11.91 | 93 | — |

Key observations:
- The gated algorithm picks winners 60% of the time at average odds ~7.25 — genuine longshots the market undervalues
- Market favourite wins only 29% of TSR-complete races, confirming these are genuinely hard-to-call races where the algorithm has a real edge
- Despite predicting on only 10% of races, the gated version generates **more total ROI** than the ungated (+313 vs +254) — all the alpha is concentrated in TSR-complete races
- ROI per race is 12.5× higher gated (+3.37) vs ungated (+0.27)

See `RatingsXGBoostAlgorithm` in `race_analytics/algorithms/ratings_xgboost.py`.

---

## Outstanding Work / Next Steps

1. **Computed speed figures**: TSR is unavailable for most races. A computed speed rating — normalising `Speed = DistanceInMeters / RaceTimeInSeconds` for going, surface, and distance using historical par times — could provide consistent TSR-like coverage across all races. This is the most impactful pending improvement.

2. **Hyperparameter tuning**: `RatingsXGBoostAlgorithm` uses default XGBoost settings (200 trees, lr=0.05, depth=4). Systematic tuning (n_estimators, max_depth, subsample, colsample_bytree) may improve performance further.

3. **Extended backtest**: 60 folds covers ~2 months. A 180–365 fold backtest would give more statistically robust ROI estimates.
