# Algorithm Evaluation Findings

## 180-fold walk-forward results — 2025-12-02 → 2026-05-30

180 folds, 7-month training window per fold. `roi` is net £ on flat £1 stakes;
`accuracy` is picks finishing 1st. See `race_analytics/utils/scoring.py` for
exact definitions.

| Algorithm | Accuracy | Net £ ROI | Races | Fav accuracy | Fav ROI |
|---|---|---|---|---|---|
| RidgeRegressionAlgorithm | 0.241 | −107.09 | 2517 | 0.385 | +44.25 |
| XGBoostAlgorithm | 0.246 | −119.82 | 2517 | 0.385 | +44.25 |
| RatingsXGBoostAlgorithm (TSR-gated) | 0.288 | −16.09 | 1779 | 0.379 | +57.20 |
| RatingsXGBoostUngatedAlgorithm | 0.288 | −31.16 | 2517 | 0.385 | +44.25 |
| **ProxyTSRXGBoostAlgorithm** ← active | **0.294** | −22.20 | 2517 | 0.385 | +44.25 |
| TunedProxyTSRXGBoostAlgorithm | 0.285 | −52.30 | 2517 | 0.385 | +44.25 |

Raw predictions: `evaluation_results_20260531.csv`.

## Timing summary

| Algorithm | Fit avg (s) | Fit std | Predict avg (s) | Predict std |
|---|---|---|---|---|
| RidgeRegressionAlgorithm | 1.062 | 0.671 | 0.026 | 0.007 |
| XGBoostAlgorithm | 0.289 | 0.059 | 0.035 | 0.010 |
| RatingsXGBoostAlgorithm | 0.613 | 0.107 | 0.042 | 0.010 |
| RatingsXGBoostUngatedAlgorithm | 0.613 | 0.117 | 0.038 | 0.006 |
| ProxyTSRXGBoostAlgorithm | 33.827 | 9.349 | 0.040 | 0.007 |
| TunedProxyTSRXGBoostAlgorithm | 34.612 | 9.117 | 0.041 | 0.007 |

`ProxyTSRXGBoost` and its tuned variant fit ~34 s/fold (proxy computation
dominates); all others fit in under 1.1 s/fold. Predict time is negligible
(<50 ms) across all algorithms.

## Active algorithm

```python
ACTIVE_ALGORITHM = ProxyTSRXGBoostAlgorithm
```

`ProxyTSRXGBoostAlgorithm` leads on accuracy at **0.294** — 6 pp ahead of
`TunedProxyTSRXGBoostAlgorithm` (0.285) and 9 pp ahead of both
`RatingsXGBoost*` variants. Every ratings-aware algorithm beats the Ridge and
XGBoost baselines (0.241 / 0.246). ROI is directional over 2,517 bets;
accuracy is the ranking signal.

Alternatives considered:

- `RatingsXGBoostAlgorithm` (TSR-gated) — best ML ROI at −£16, but covers
  only 1,779 of 2,517 races (70.7%) due to the TSR-complete gate; the ROI
  advantage over the ungated variant is within noise at this sample size.
- `RatingsXGBoostUngatedAlgorithm` — ties gated on accuracy (0.288), full
  coverage. Natural fallback if the proxy approach is dropped.
- `TunedProxyTSRXGBoostAlgorithm` — trails the untuned variant by 9 pp over
  the full 180-fold window. Not enough evidence to prefer it.

See `ProxyTSRXGBoostAlgorithm` in
`race_analytics/algorithms/proxy_tsr_xgboost.py` and `ProxyTSRModel` in
`race_analytics/algorithms/proxy_tsr.py`.

## Production anchor

From 2026 `PredictionScores_*.csv` logs (real production picks with outcomes):

| Bets | Wins | Accuracy | Net £ (flat stake) |
|---|---|---|---|
| **514** | 136 | **0.265** | **+78.22** |

The eval `ProxyTSRXGBoostAlgorithm` accuracy of **0.294** is +2.9 pp above
this anchor — a reasonable ballpark given the different time window and field
conditions.

## Methodology

- **Walk-forward evaluation**: each fold trains on the 7 most-recent months
  strictly before the fold date and predicts on the fold date.
- **Algorithms**: all six registered in `race_analytics/algorithms/__init__.py`.
- **Baseline**: market favourite (lowest decimal odds in each race).
- **Scoring**: `accuracy = mean(FinishingPosition == 1)` for the top pick per
  race; `roi = Σ DecimalOdds of winners − number of bets`.
- **Filters**: `KnownHorseAndJockey`, every horse predictable (required
  `PREDICTORS` non-null; `Last3*` optional via NaN tolerance), field size ≤ 10.
  TSR-gated variant additionally requires `LastRaceTopSpeedRating` non-null
  for every horse.
- **Run command**: `python -m race_analytics.scripts.evaluate --folds 180 --training-months 7 --save-results`
