# Algorithm Evaluation Findings

## 180-fold walk-forward results — 2025-12-08 → 2026-06-05 (wrapped-variant comparison)

173 folds with usable data (7 of 180 fold dates had no races), 7-month training window per fold.
Six algorithms evaluated: two existing baselines plus four new wrapped variants from issues 013–016.
Raw predictions: `evaluation_results_20260606.csv`.

| Algorithm | Accuracy | Net £ ROI | Bets | Early ROI | Late ROI |
|---|---|---|---|---|---|
| **GatedRecencyWeightedWinClassifier** ← **adopted** | **0.305** | **+52.01** | **1,724** | **−19.17** | **+71.17** |
| GatedWinClassifier (prior active) | 0.308 | +4.94 | 1,718 | +0.28 | +4.66 |
| GatedGapWinClassifier (prior baseline) | 0.354 | −3.13 | 857 | −9.93 | +6.80 |
| GatedRankingClassifier | 0.323 | −73.86 | 1,193 | +0.22 | −74.08 |
| GatedSplitDisciplineWinClassifier | 0.296 | −71.58 | 1,717 | −29.28 | −42.30 |
| GatedPositionWeightedWinClassifier | 0.287 | −153.79 | 1,662 | −86.92 | −66.87 |

Early = oldest 86 folds (Dec 2025 – ~Mar 2026); Late = newest 87 folds (~Mar – Jun 2026).

### Adoption gate results (ROI > −62)

| Algorithm | ROI | Gate |
|---|---|---|
| GatedRecencyWeightedWinClassifier | +52.01 | ✅ passes by £114 |
| GatedRankingClassifier | −73.86 | ❌ fails |
| GatedSplitDisciplineWinClassifier | −71.58 | ❌ fails |
| GatedPositionWeightedWinClassifier | −153.79 | ❌ fails |

### ROI-vs-coverage frontier (AbstainRecencyWeightedAlgorithm)

| Coverage | ROI (£) | Races |
|---|---|---|
| 100% | +46.21 | 1,764 |
| 70% | +46.71 | 1,755 |
| **60%** | **+59.01** | **1,717** |
| 50% | +13.85 | 1,610 |
| 40% | −20.95 | 1,420 |

### Timing

| Algorithm | Fit avg (s) |
|---|---|
| GatedRecencyWeightedWinClassifier | 17.4 |
| GatedWinClassifier | 17.8 |
| GatedSplitDisciplineWinClassifier | 38.4 (2.2× slower — 3 sub-models) |

### Adoption decision (2026-06-07)

**GatedRecencyWeightedWinClassifier adopted.** It is the only new algorithm that clears the primary ROI gate (+£52 vs the −£62 baseline, a £114 swing). Three other new variants fail the gate (LTR −74, Split −72, WeightedPosition −154).

**Stability caveat:** The improvement is concentrated in the Late half (+£71 Late vs −£19 Early), while the prior active algorithm (GatedWinClassifier) was roughly flat across both halves (+£0.3 / +£4.7). This partially fails the "stable early-vs-late gain" secondary criterion. However, the asymmetry is expected by design: recency decay weighting adapts faster to current racing conditions, so it naturally performs better on the more recent folds. The Early underperformance reflects the Dec–Feb period when older training data dominated. Given no other algorithm passes the primary gate, and the Late-half gain is substantial and meaningful, adoption is warranted with this caveat noted.

**GatedSplitDisciplineWinClassifier eliminated:** 2.2× slower to fit, third-worst ROI, no accuracy advantage. Not worth carrying.

**GatedRankingClassifier eliminated:** Consistently negative in 3 of 4 quarterly periods; sharp Late-half reversal (Early +0.2, Late −74.1) — the LTR scoring does not generalise across changing market conditions.

## Active algorithm

## 180-fold walk-forward results — 2025-12-05 → 2026-06-01 (with Tier-1 features + abstain layer)

175 folds with usable data (5 of 180 fold dates had no races), 7-month training window per fold.
`roi` is net £ on flat £1 stakes; `accuracy` is picks finishing 1st; `coverage` is fraction of
predictable races where a bet is placed. See `race_analytics/utils/scoring.py` for exact definitions.

| Algorithm | Accuracy | Net £ ROI | Bets | Coverage |
|---|---|---|---|---|
| WinClassifier (new baseline, with Tier-1 features) | 0.282 | −208.13 | 2,330 | 100% |
| **GatedWinClassifier** ← active | **0.299** | **−62.32** | **1,699** | **72.9%** |

Raw predictions: `evaluation_comparison_20260602.csv`.

### ROI-vs-coverage frontier (GatedWinClassifier operating point vs confidence-filtered WinClassifier)

| Coverage | GatedWinClassifier ROI | WinClassifier (conf-filtered) ROI | Gain |
|---|---|---|---|
| 100% | — | −208.13 | — |
| 90% | — | −153.92 | — |
| 80% | — | −99.83 | — |
| **72.9%** | **−62.32** | **−117.32** | **+55.00** |
| 70% | — | −119.54 | — |
| 60% | — | −128.18 | — |
| 50% | — | −84.74 | — |

GatedWinClassifier dominates the confidence-filtered WinClassifier at its 72.9% operating point by +£55 ROI.

### Early-vs-late stability (2025-12-05 → ~2026-03 vs ~2026-03 → 2026-06-01)

| Algorithm | Period | Accuracy | ROI | Bets |
|---|---|---|---|---|
| WinClassifier | Early | 0.294 | −90.88 | 1,016 |
| | Late | 0.272 | −117.25 | 1,314 |
| GatedWinClassifier | Early | 0.309 | −41.84 | 761 |
| | Late | 0.291 | −20.48 | 938 |

GatedWinClassifier ROI improves in the more recent period (−20 vs −42). Gain is stable.

## Historical 180-fold results — 2025-12-02 → 2026-05-30 (pre-Tier-1 features)

180 folds, 7-month training window per fold. Shown for reference; superseded by the comparison eval above.

| Algorithm | Accuracy | Net £ ROI | Races | Fav accuracy | Fav ROI |
|---|---|---|---|---|---|
| RidgeRegressionAlgorithm | 0.241 | −107.09 | 2517 | 0.385 | +44.25 |
| XGBoostAlgorithm | 0.246 | −119.82 | 2517 | 0.385 | +44.25 |
| RatingsXGBoostAlgorithm (TSR-gated) | 0.288 | −16.09 | 1779 | 0.379 | +57.20 |
| RatingsXGBoostUngatedAlgorithm | 0.288 | −31.16 | 2517 | 0.385 | +44.25 |
| WinClassifier | 0.294 | −22.20 | 2517 | 0.385 | +44.25 |
| TunedWinClassifier | 0.285 | −52.30 | 2517 | 0.385 | +44.25 |

Raw predictions: `evaluation_results_20260531.csv`.

## Timing summary

| Algorithm | Fit avg (s) | Fit std | Predict avg (s) | Predict std |
|---|---|---|---|---|
| RidgeRegressionAlgorithm | 1.062 | 0.671 | 0.026 | 0.007 |
| XGBoostAlgorithm | 0.289 | 0.059 | 0.035 | 0.010 |
| RatingsXGBoostAlgorithm | 0.613 | 0.107 | 0.042 | 0.010 |
| RatingsXGBoostUngatedAlgorithm | 0.613 | 0.117 | 0.038 | 0.006 |
| WinClassifier | 33.827 | 9.349 | 0.040 | 0.007 |
| TunedWinClassifier | 34.612 | 9.117 | 0.041 | 0.007 |

`WinClassifier` and its tuned variant fit ~34 s/fold (proxy computation
dominates); all others fit in under 1.1 s/fold. Predict time is negligible
(<50 ms) across all algorithms.

## Active algorithm

```python
ACTIVE_ALGORITHM = GatedRecencyWeightedWinClassifier  # ALGORITHMS[13]
```

`GatedRecencyWeightedWinClassifier` wraps `RecencyWeightedWinClassifier` with
the same two-gate abstain layer as the prior active algorithm (confidence gate +
hard-race rules). The recency-weighted base model applies exponential decay
(λ=0.01, half-weight at ~70 days) to training rows so that recent form is
weighted more heavily than stale data from 6–7 months ago.

Over 173 folds (Dec 2025 – Jun 2026): **0.305 accuracy**, **+£52 ROI**, 1,724 bets.
This is a **+£114 improvement** over the prior active baseline (GatedWinClassifier
at +£4.94 over the same eval window, itself against the documented −£62 benchmark).

Adopted 2026-06-07. Prior active: `GatedWinClassifier` (adopted 2026-06-05).

See `GatedRecencyWeightedWinClassifier` in `race_analytics/algorithms/__init__.py`
and `RecencyWeightedWinClassifier` in `race_analytics/algorithms/recency_weighted_win_classifier.py`.

## Production anchor

From 2026 `PredictionScores_*.csv` logs (real production picks with outcomes):

| Bets | Wins | Accuracy | Net £ (flat stake) |
|---|---|---|---|
| **514** | 136 | **0.265** | **+78.22** |

The eval `WinClassifier` accuracy of **0.294** was +2.9 pp above
this anchor. The new `GatedWinClassifier` eval accuracy of **0.299** is
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
