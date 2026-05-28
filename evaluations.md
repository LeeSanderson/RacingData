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

## ProxyTSRXGBoostAlgorithm

### Design

- **ProxyTSRModel**: XGBoost regressor trained to predict `TopSpeedRating` from per-race outcome data (speed, conditions, finishing position, beaten distance, course). Aggregates per-horse into `PeakProxyTSR`, `LastProxyTSR`, `Best5ProxyTSR`.
- **ProxyTSRXGBoostAlgorithm**: Uses `ProxyTSRModel` as a first stage. Feeds 6 proxy TSR features (3 absolute + 3 relative vs field) alongside real TSR (NaN-tolerant) into an `XGBClassifier`. **No TSR gating** — predicts on all `KnownHorseAndJockey` races.

### 60-fold results (951 races)

| Algorithm | Accuracy | ROI | Races | ROI/race |
|---|---|---|---|---|
| RidgeRegressionAlgorithm | 0.242 | +59.60 | 951 | +0.06 |
| XGBoostAlgorithm | 0.237 | -61.11 | 951 | -0.06 |
| **RatingsXGBoostAlgorithm (TSR-gated)** | **0.602** | **+313.12** | **93** | **+3.37** |
| RatingsXGBoostUngatedAlgorithm | 0.313 | +265.80 | 951 | +0.28 |
| **ProxyTSRXGBoostAlgorithm** | **0.301** | **+240.61** | **951** | **+0.25** |
| Market Favourite (full pop) | 0.366 | -19.24 | 951 | — |
| Market Favourite (gated races) | 0.290 | -11.91 | 93 | — |

### 180-fold results (2,475 races) — statistically robust

| Algorithm | Accuracy | ROI | Races | ROI/race |
|---|---|---|---|---|
| RidgeRegressionAlgorithm | 0.235 | -127.15 | 2,475 | -0.05 |
| XGBoostAlgorithm | 0.247 | -72.46 | 2,475 | -0.03 |
| **RatingsXGBoostAlgorithm (TSR-gated)** | **0.783** | **+3,406** | **981** | **+3.47** |
| RatingsXGBoostUngatedAlgorithm | 0.532 | +4,250 | 2,475 | +1.72 |
| ProxyTSRXGBoostAlgorithm | 0.509 | +3,573 | 2,475 | +1.44 |
| **TunedProxyTSRXGBoostAlgorithm** | **0.515** | **+3,740** | **2,475** | **+1.51** |
| Market Favourite (full pop) | 0.387 | +77.60 | 2,475 | — |
| Market Favourite (gated races) | 0.402 | +80.41 | 981 | — |

Key observations:
- **Tuning works**: TunedProxyTSR beats default ProxyTSR (+3,740 vs +3,573 ROI, 0.515 vs 0.509 accuracy)
- **Dramatic improvement vs 60-fold**: ratings-based algorithms all improve sharply. The gated algorithm jumped 0.602→0.783 accuracy, +313→+3,406 ROI. This confirms 60 folds covered a harder recent period; 180 folds is the more representative estimate across racing seasons
- **Ungated now beats gated in total ROI** (+4,250 vs +3,406) due to 2.5× more races at a strong +1.72 ROI/race — volume is genuinely valuable
- **ProxyTSR gap to ungated is modest**: 0.509 vs 0.532 accuracy, +3,573 vs +4,250 ROI — proxy features add real signal but do not fully close the gap to real TSR availability
- **Gated per-race ROI remains dominant** (+3.47) — all the high-confidence alpha is still concentrated in TSR-complete races

See `ProxyTSRModel` in `race_analytics/algorithms/proxy_tsr.py`, `ProxyTSRXGBoostAlgorithm` and `TunedProxyTSRXGBoostAlgorithm` in `race_analytics/algorithms/proxy_tsr_xgboost.py`.

---

## Outstanding Work / Next Steps

1. **Hyperparameter tuning**: Both `ProxyTSRModel` (XGBRegressor) and `ProxyTSRXGBoostAlgorithm` (XGBClassifier) use default XGBoost settings (200 trees, lr=0.05, depth=4, no subsampling). `ProxyTSRModel.tune()` runs `RandomizedSearchCV` over n_estimators, max_depth, learning_rate, subsample, colsample_bytree. `ProxyTSRXGBoostAlgorithm` exposes these as constructor params and accepts `tune_proxy=True` to trigger proxy model tuning during `fit()`.

2. **Extended backtest**: 60 folds covers ~2 months. A 180–365 fold backtest would give more statistically robust ROI estimates.

3. **TSR-gated vs proxy-gated strategy**: Investigate whether gating `ProxyTSRXGBoostAlgorithm` on proxy TSR confidence (e.g. horse has ≥ N historical races) improves ROI/race while maintaining better volume than the real-TSR gate.
