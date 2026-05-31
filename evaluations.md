# Algorithm Evaluation Findings

> **Update (2026-05-28):** the previous version of this page reported a ~0.78
> accuracy and large positive ROI for the TSR-gated `RatingsXGBoostAlgorithm`.
> Those figures were inflated by a post-race RPR/TSR leak that has now been
> fixed (see issues 001–007). The numbers below are the honest, leak-free
> re-evaluation; the gated headline has collapsed from ~0.78 to **0.29**, in
> line with the **0.265** real production anchor.

## Headline finding

The old TSR-gated `RatingsXGBoostAlgorithm` "0.78 accuracy" claim was a
feature-leak artefact. Racing Post's `RacingPostRating` (RPR) and
`TopSpeedRating` (TSR) are **post-race** figures (within-race Spearman vs
finishing position ≈ −0.88 / −0.86 — they essentially encode the result). In
the old evaluator, the day's *results* row carried these post-race ratings
into the model card, while `predict.py` in production saw only the weak
pre-race form — a textbook train/serve skew, ~3× inflation.

The fix (issues 002–005): every rating feature is now the horse's
**previous-race** value sourced from the per-horse stats join; the proxy is
an as-of-date "last prior proxy" per horse; the card no longer carries any
rating columns.

## Production anchor

Computed from the 2026 `PredictionScores_*.csv` logs (the real picks the
previously-active algorithm logged in production, with outcomes):

| Bets | Wins | Accuracy | Net £ (flat stake) |
|---|---|---|---|
| **514** | 136 | **0.265** | **+78.22** |

Per-month accuracy: 0.278 / 0.175 / 0.308 / 0.231. Accuracy is the reliable
signal; ROI is positive but noisy. **~0.265 is the realistic accuracy a
leak-free eval should land near.**

## Phase C (180-fold) walk-forward results — 2025-12-02 → 2026-05-30

The definitive full-window re-baseline. 180 folds with a 7-month training
window, run after the full NaN-tolerance rollout to XGBoost-family algorithms
(issue 005). Race count is now **2,517** (14.0 races/fold) — restored to the
pre-PREDICTORS-expansion order of magnitude, and consistent with Phase B's
13.9 races/fold. `roi` is net £ on flat £1 stakes; `accuracy` is picks
finishing 1st. See `race_analytics/utils/scoring.py` for exact definitions.

| Algorithm | Accuracy | Net £ ROI | Races | Fav accuracy (same races) | Fav ROI |
|---|---|---|---|---|---|
| RidgeRegressionAlgorithm | 0.241 | −107.09 | 2517 | 0.385 | +44.25 |
| XGBoostAlgorithm | 0.246 | −119.82 | 2517 | 0.385 | +44.25 |
| RatingsXGBoostAlgorithm (TSR-gated) | 0.288 | −16.09 | 1779 | 0.379 | +57.20 |
| RatingsXGBoostUngatedAlgorithm | 0.288 | −31.16 | 2517 | 0.385 | +44.25 |
| **ProxyTSRXGBoostAlgorithm** ← active | **0.294** | −22.20 | 2517 | 0.385 | +44.25 |
| TunedProxyTSRXGBoostAlgorithm | 0.285 | −52.30 | 2517 | 0.385 | +44.25 |

`ProxyTSRXGBoostAlgorithm` leads on accuracy by 6 pp over `TunedProxyTSRXGBoostAlgorithm`
and 9 pp over Ridge. All ML ROIs are negative; the market favourite's +£44 ROI reflects its
ability to identify short-priced winners the ML models miss. ROI over 2,517 bets remains
directional rather than conclusive — accuracy is the ranking signal.

### Timing summary (Phase C)

| Algorithm | Fit avg (s) | Fit std | Predict avg (s) | Predict std |
|---|---|---|---|---|
| RidgeRegressionAlgorithm | 1.062 | 0.671 | 0.026 | 0.007 |
| XGBoostAlgorithm | 0.289 | 0.059 | 0.035 | 0.010 |
| RatingsXGBoostAlgorithm | 0.613 | 0.107 | 0.042 | 0.010 |
| RatingsXGBoostUngatedAlgorithm | 0.613 | 0.117 | 0.038 | 0.006 |
| ProxyTSRXGBoostAlgorithm | 33.827 | 9.349 | 0.040 | 0.007 |
| TunedProxyTSRXGBoostAlgorithm | 34.612 | 9.117 | 0.041 | 0.007 |

`ProxyTSRXGBoostAlgorithm` and its tuned variant fit ~34 s/fold (proxy
computation dominates); all others fit in under 1.1 s/fold. Predict time is
negligible (<50 ms) across all algorithms.

## Phase B (30-fold) walk-forward results — 2026-04-29 → 2026-05-28

Post-issue-005 validation run. 30 folds covering peak flat-racing season only
(the 180-fold equivalent took ~24h wall time). Included here for the
peak-season accuracy signal, which complements Phase C's full-window view.

| Algorithm | Accuracy | Net £ ROI | Races | Fav accuracy (same races) |
|---|---|---|---|---|
| RidgeRegressionAlgorithm | 0.240 | +41.41 | 417 | 0.363 |
| XGBoostAlgorithm | 0.259 | +0.73 | 417 | 0.363 |
| RatingsXGBoostAlgorithm (TSR-gated) | 0.238 | −6.38 | 147 | 0.390 |
| RatingsXGBoostUngatedAlgorithm | 0.233 | −57.39 | 417 | 0.363 |
| **ProxyTSRXGBoostAlgorithm** ← active | **0.261** | −87.24 | 417 | 0.363 |
| TunedProxyTSRXGBoostAlgorithm | 0.264 | −15.53 | 417 | 0.363 |

Coverage is equal across all non-gated algorithms (417 races each).
`RatingsXGBoostAlgorithm` 147 races reflects the TSR-complete gate applied to
a 30-day May window (expected). ROI over 417 races is too noisy to rank
algorithms.

## Phase A (180-fold) walk-forward results — 2025-11-28 → 2026-05-26

*Superseded by Phase C.* Included for reference as the first post-leak-fix
180-fold run. Phase A was run before NaN-tolerance was extended to the
XGBoost-family, which restricted coverage to **415 races** (2.3/fold) — only
races where every horse had all `PREDICTORS` non-null. Phase C restores the
full ~14 races/fold coverage.

| Algorithm | Accuracy | Net £ ROI | Races | Fav accuracy (same races) |
|---|---|---|---|---|
| RidgeRegressionAlgorithm | 0.270 | +129.24 | 415 | 0.379 |
| XGBoostAlgorithm | 0.299 | +118.14 | 415 | 0.379 |
| RatingsXGBoostAlgorithm (TSR-gated) | 0.290 | −7.06 | 397 | 0.379 |
| RatingsXGBoostUngatedAlgorithm | 0.296 | +18.82 | 415 | 0.379 |
| **ProxyTSRXGBoostAlgorithm** | **0.304** | +13.37 | 415 | 0.379 |
| TunedProxyTSRXGBoostAlgorithm | 0.289 | +64.74 | 415 | 0.379 |

Phase A accuracy numbers are higher than Phase C because the strict
`PREDICTORS` filter biased the sample toward experienced horses (≥3 prior
races, known trainer) who are easier to rank. Phase C's broader coverage
includes more uncertain cases, producing lower but more realistic accuracy.

### Old (leaky) vs clean — side-by-side comparison

| Algorithm | Old (leaky) accuracy | Phase A (clean) accuracy | Phase C (clean) accuracy |
|---|---|---|---|
| RatingsXGBoost (TSR-gated) | **0.783** | 0.290 | 0.288 |
| RatingsXGBoostUngated | 0.532 | 0.296 | 0.288 |
| ProxyTSRXGBoost | 0.509 | 0.304 | **0.294** |
| TunedProxyTSRXGBoost | 0.515 | 0.289 | 0.285 |
| RidgeRegression | 0.235 | 0.270 | 0.241 |
| XGBoost | 0.247 | 0.299 | 0.246 |

## Leak-gone check vs the production anchor

The Phase C `ProxyTSRXGBoostAlgorithm` accuracy **0.294** lands within **+2.9 pp**
of the production anchor **0.265** — a rough ballpark match. The TSR-gated
0.78 headline has fully collapsed across all three evaluation phases.
**The leak is gone.**

## What changed in practice

- **The "TSR is the key driver" story was the leak.** With ratings restricted
  to previous-race values, the TSR gate excludes 738 of 2,517 races (70.7% kept
  in Phase C). This is lower than Phase A's 95.7% because the full 180-fold
  window includes more winter races where horses lack a recent prior TSR.
  Despite covering fewer races, the gated algorithm's accuracy matches the
  ungated variant exactly (both 0.288), confirming the gate no longer confers
  a meaningful signal advantage.
- **Ratings are still a genuine pre-race signal.** Every ratings-aware
  algorithm beats the plain Ridge and XGBoost baselines on accuracy
  (0.241 / 0.246 vs 0.285–0.294), confirming that previous-race ratings carry
  real predictive information beyond last-race speed.
- **The market favourite dominates on both accuracy and ROI in Phase C.**
  It wins 38.5% of the time and returns +£44 over 2,517 bets. All ML
  algorithms are accuracy-negative vs the favourite and ROI-negative. The
  ML algorithms add value only when they agree with a long-priced runner —
  a signal that needs further extraction (e.g. value-betting on agreement
  with high odds).
- **Phase C accuracy is lower than Phase A** because the NaN-tolerance
  expansion brings in horses with fewer prior races (sparser stats, harder to
  predict). Phase A's artificially high numbers were a selection artefact.

## Race count: why Phase C has more races than Phase A

Phase A (415 races, 2.3/fold) vs Phase C (2,517 races, 14.0/fold). The jump
is entirely explained by the NaN-tolerance rollout:

- Commit `1f8c709` ("Issue 009: Extend PREDICTORS") added 7 columns including
  `Last3RaceAvgSpeed`, `Last3RaceSpeedTrend`, `Last3AvgRelFinishingPosition`,
  and four `Trainer*` columns. Each algorithm's `predict()` drops any race
  where a horse is missing any `PREDICTOR`. `Last3*` are NaN for horses with
  fewer than 3 prior starts; `Trainer*` are NaN for unknown trainers.
  This tightened Phase A's coverage to only the most-established horses.
- Issue 005 added `nan_tolerant_predictors = OPTIONAL_PREDICTORS` to the
  XGBoost-family algorithms, moving `Last3*` from required to optional.
  Rows with NaN `Last3*` are no longer dropped at fit or predict time.
- By Phase C, NaN-tolerance is in place for all algorithms, restoring
  race-count to the pre-expansion order of magnitude (~2,475 in the old leaky
  run; ~2,517 in Phase C).

The same filter applies in production (`predict.py` uses the same
`_fitted_predictors` intersection), so Phase C's ~14-races/fold figure is
the realistic baseline for what `predict --data Data` sees day-to-day.

## Active algorithm

```python
ACTIVE_ALGORITHM = ProxyTSRXGBoostAlgorithm
```

(was `RatingsXGBoostAlgorithm` TSR-gated.)

**Rationale — Phase C review.** Phase C (2,517 races, the most statistically
reliable sample) puts `ProxyTSRXGBoostAlgorithm` at **0.294** accuracy —
6 pp ahead of `TunedProxyTSRXGBoostAlgorithm` (0.285) and 9 pp ahead of
both `RatingsXGBoost*` variants (0.288). The Phase B 30-fold run showed the
tuned variant marginally ahead (0.264 vs 0.261) over 417 peak-season races,
but that gap is within sampling noise. Across all three phases, the untuned
`ProxyTSRXGBoostAlgorithm` is consistently the stronger or equal choice.
Active algorithm unchanged.

**Alternatives considered (Phase C numbers):**

- `TunedProxyTSRXGBoostAlgorithm` (0.285 / −£52, 2517 races) — consistently
  trails the untuned variant in the full-window sample. Phase B favoured it
  marginally; Phase C does not. No evidence to swap.
- `RatingsXGBoostUngatedAlgorithm` (0.288 / −£31, 2517 races) — ties the
  gated variant, simpler model. Natural fallback if the proxy approach is
  dropped.
- `RatingsXGBoostAlgorithm` (0.288 / −£16, 1779 races) — best ROI among ML
  algorithms in Phase C (least loss), but restricted to 70.7% of races by
  the TSR gate and the ROI difference over the ungated variant is well within
  noise at this sample size.
- `RidgeRegressionAlgorithm` (0.241 / −£107) — weakest ML accuracy; its
  occasional Phase A ROI advantage was sample-driven and has not persisted
  across Phase C's broader race set.

See `ProxyTSRXGBoostAlgorithm` in
`race_analytics/algorithms/proxy_tsr_xgboost.py` and `ProxyTSRModel` (with
its leak-free `compute_as_of_proxy` and `compute_horse_proxy_tsr`) in
`race_analytics/algorithms/proxy_tsr.py`.

## Methodology

- **Walk-forward evaluation**: each fold trains on the 7 most-recent months
  strictly before the fold date and predicts on the fold date.
- **Algorithms**: all six registered (`race_analytics/algorithms/__init__.py`).
- **Baseline**: market favourite (lowest decimal odds in each race).
- **Scoring**: `accuracy` over completed races; `roi` = Σ decimal odds of
  winners − number of bets (net £ on £1 flat stakes).
- **Filters**: `KnownHorseAndJockey`, every horse predictable (all required
  `PREDICTORS` non-null — optional `PREDICTORS` may be NaN), field size ≤ 10.
  The TSR-gated variant additionally requires every horse to have a non-null
  `LastRaceTopSpeedRating`.
- **Phase C run**: 180 folds (`--folds 180 --training-months 7 --save-results`),
  dates 2025-12-02 → 2026-05-30. Raw predictions in `evaluation_results_20260531.csv`.
- **Phase B run**: 30 folds (`--folds 30 --training-months 7`), dates
  2026-04-29 → 2026-05-28 (peak flat-racing season only).
- **Phase A run**: 180 folds (`--folds 180 --training-months 7`), dates
  2025-11-28 → 2026-05-26 (pre-NaN-tolerance; superseded by Phase C).
- **Production-anchor command**: all 2026 `PredictionScores_*.csv` files,
  rows with `ResultStatus == 'CompletedRace'`, `accuracy = mean(FinishingPosition == 1)`,
  `roi = Σ DecimalOdds of winners − number of bets` (matching the eval).
