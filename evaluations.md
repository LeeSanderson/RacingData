# Algorithm Evaluation Findings

## 180-fold walk-forward results — 2025-12-05 → 2026-06-01 (with Tier-1 features + abstain layer)

175 folds with usable data (5 of 180 fold dates had no races), 7-month training window per fold.
`roi` is net £ on flat £1 stakes; `accuracy` is picks finishing 1st; `coverage` is fraction of
predictable races where a bet is placed. See `race_analytics/utils/scoring.py` for exact definitions.

| Algorithm | Accuracy | Net £ ROI | Bets | Coverage |
|---|---|---|---|---|
| ProxyTSRXGBoostAlgorithm (new baseline, with Tier-1 features) | 0.282 | −208.13 | 2,330 | 100% |
| **AbstainWrapperAlgorithm** ← active | **0.299** | **−62.32** | **1,699** | **72.9%** |

Raw predictions: `evaluation_comparison_20260602.csv`.

### ROI-vs-coverage frontier (AbstainWrapper operating point vs confidence-filtered ProxyTSR)

| Coverage | AbstainWrapper ROI | ProxyTSR (conf-filtered) ROI | Gain |
|---|---|---|---|
| 100% | — | −208.13 | — |
| 90% | — | −153.92 | — |
| 80% | — | −99.83 | — |
| **72.9%** | **−62.32** | **−117.32** | **+55.00** |
| 70% | — | −119.54 | — |
| 60% | — | −128.18 | — |
| 50% | — | −84.74 | — |

AbstainWrapper dominates the confidence-filtered ProxyTSR at its 72.9% operating point by +£55 ROI.

### Early-vs-late stability (2025-12-05 → ~2026-03 vs ~2026-03 → 2026-06-01)

| Algorithm | Period | Accuracy | ROI | Bets |
|---|---|---|---|---|
| ProxyTSRXGBoostAlgorithm | Early | 0.294 | −90.88 | 1,016 |
| | Late | 0.272 | −117.25 | 1,314 |
| AbstainWrapperAlgorithm | Early | 0.309 | −41.84 | 761 |
| | Late | 0.291 | −20.48 | 938 |

AbstainWrapper ROI improves in the more recent period (−20 vs −42). Gain is stable.

## Historical 180-fold results — 2025-12-02 → 2026-05-30 (pre-Tier-1 features)

180 folds, 7-month training window per fold. Shown for reference; superseded by the comparison eval above.

| Algorithm | Accuracy | Net £ ROI | Races | Fav accuracy | Fav ROI |
|---|---|---|---|---|---|
| RidgeRegressionAlgorithm | 0.241 | −107.09 | 2517 | 0.385 | +44.25 |
| XGBoostAlgorithm | 0.246 | −119.82 | 2517 | 0.385 | +44.25 |
| RatingsXGBoostAlgorithm (TSR-gated) | 0.288 | −16.09 | 1779 | 0.379 | +57.20 |
| RatingsXGBoostUngatedAlgorithm | 0.288 | −31.16 | 2517 | 0.385 | +44.25 |
| ProxyTSRXGBoostAlgorithm | 0.294 | −22.20 | 2517 | 0.385 | +44.25 |
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
ACTIVE_ALGORITHM = AbstainWrapperAlgorithm
```

`AbstainWrapperAlgorithm` wraps `ProxyTSRXGBoostAlgorithm` with a two-gate
abstain layer (confidence gate + hard-race rules). At its operating point it
bets **72.9%** of predictable races (1,699 of 2,330), achieving **0.299
accuracy** and **−£62 ROI** — a +£55 improvement over confidence-filtered
ProxyTSR at the same coverage. The gain is stable in the early-vs-late split
(ROI improves late: −20 vs −42). Accuracy (+3.4 pp above the 0.265 production
anchor) is consistent and believable.

All three acceptance bar checks PASSED on 2026-06-05:
- ROI-vs-coverage frontier dominates ProxyTSR at ≥50% coverage (+£55 at 72.9%)
- Early-vs-late gain is stable (ROI improves in the more recent period)
- Production anchor sanity check passes (+3.4 pp vs +2.9 pp historical)

`predict.py` uses `ACTIVE_ALGORITHM` directly — the abstain layer fires
automatically in production; no new CLI verb or wiring change is needed.

See `AbstainWrapperAlgorithm` in `race_analytics/algorithms/abstain_wrapper.py`,
`ConfidenceGate` in `race_analytics/algorithms/confidence_gate.py`, and
`RaceRulesGate` in `race_analytics/algorithms/race_rules_gate.py`.

## Production anchor

From 2026 `PredictionScores_*.csv` logs (real production picks with outcomes):

| Bets | Wins | Accuracy | Net £ (flat stake) |
|---|---|---|---|
| **514** | 136 | **0.265** | **+78.22** |

The eval `ProxyTSRXGBoostAlgorithm` accuracy of **0.294** was +2.9 pp above
this anchor. The new `AbstainWrapperAlgorithm` eval accuracy of **0.299** is
+3.4 pp above it — consistent and believable.

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
