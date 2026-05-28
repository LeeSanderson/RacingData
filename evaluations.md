# Algorithm Evaluation Findings

> **Update (2026-05-28):** the previous version of this page reported a ~0.78
> accuracy and large positive ROI for the TSR-gated `RatingsXGBoostAlgorithm`.
> Those figures were inflated by a post-race RPR/TSR leak that has now been
> fixed (see `issues/prd.md`, issues 001–007). The numbers below are the
> honest, leak-free re-evaluation; the gated headline has collapsed from
> ~0.78 to **0.29**, in line with the **0.265** real production anchor.

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

## 180-fold leak-free walk-forward results

Fold dates 2025-11-28 → 2026-05-26, 7-month training window per fold (the
PRD-defined re-baseline run). `roi` is net £ on flat £1 stakes
(Σ decimal-odds of winners − number of bets); `accuracy` is picks finishing
1st divided by picks on completed races. See
`race_analytics/utils/scoring.py` for the exact definitions.

| Algorithm | Accuracy | Net £ ROI | Races | Fav accuracy (same races) |
|---|---|---|---|---|
| RidgeRegressionAlgorithm | 0.270 | +129.24 | 415 | 0.379 |
| XGBoostAlgorithm | 0.299 | +118.14 | 415 | 0.379 |
| RatingsXGBoostAlgorithm (TSR-gated) | 0.290 | −7.06 | 397 | 0.379 |
| RatingsXGBoostUngatedAlgorithm | 0.296 | +18.82 | 415 | 0.379 |
| **ProxyTSRXGBoostAlgorithm** ← active | **0.304** | +13.37 | 415 | 0.379 |
| TunedProxyTSRXGBoostAlgorithm | 0.289 | +64.74 | 415 | 0.379 |

### Old (leaky) vs new (clean) — the same 180-fold table side-by-side

| Algorithm | Old (leaky) accuracy | New (clean) accuracy |
|---|---|---|
| RatingsXGBoost (TSR-gated) | **0.783** | **0.290** |
| RatingsXGBoostUngated | 0.532 | 0.296 |
| ProxyTSRXGBoost | 0.509 | 0.304 |
| TunedProxyTSRXGBoost | 0.515 | 0.289 |
| RidgeRegression | 0.235 | 0.270 |
| XGBoost | 0.247 | 0.299 |

## Leak-gone check vs the production anchor

The clean TSR-gated accuracy **0.290** lands within **+2.5 pp** of the
production anchor **0.265** — a rough ballpark match, which is the only
sanity-check the PRD asked for (a head-to-head replay was explicitly out of
scope). The TSR-gated 0.78 headline has fully collapsed. **The leak is gone.**

## What changed in practice

- **The "TSR is the key driver" story was the leak.** With ratings restricted
  to previous-race values, gating on TSR coverage now barely excludes anything
  (397 / 415 races = **95.7%** kept, vs the old 981 / 2,475 = 39.6%). Every
  horse with any prior race has a clean `LastRaceTopSpeedRating`, so the gate
  buys ~nothing.
- **Ratings are still a genuine pre-race signal.** Every ratings-aware
  algorithm beats the Ridge baseline on accuracy (0.270 vs 0.289–0.304),
  confirming the PRD expectation that previous-race ratings beat last-race
  speed alone.
- **Every ML algorithm now beats the old Ridge / XGBoost baselines**
  (0.270 / 0.299 vs the old 0.235 / 0.247). The "wrong target variable"
  diagnosis in the previous version of this document — that the speed-target
  models learned race conditions, not horse quality — still stands; switching
  to a `Wins`-target classifier remains the right call independent of the leak.
- **The market favourite still wins on accuracy** (0.379) but the ML algos
  all beat it on net £ ROI — they pick at longer odds and capture value when
  the favourite is mispriced.

## Note on sample size

The new 180-fold sample is **415 races** vs the old run's **2,475**. This is a
property of the current data state plus the existing `KnownHorseAndJockey` and
`OriginalCount == PredictableCount` (whole-race predictability) filters; it is
**not** caused by the leakage fix — the untouched Ridge baseline shows the
same per-fold race counts as the corrected algorithms. The smaller sample is
still meaningful (and ~3× the original 14-fold baseline) but the per-algorithm
ROI gaps should be read as directional rather than precise.

## Active algorithm

```python
ACTIVE_ALGORITHM = ProxyTSRXGBoostAlgorithm
```

(was `RatingsXGBoostAlgorithm` TSR-gated.)

**Rationale.** On leak-free numbers the previously-active gated algorithm is
the worst ML choice in the table (−£7 ROI, the gate excludes only 18 / 415
races). `ProxyTSRXGBoostAlgorithm` has the highest ML accuracy (**0.304**)
with positive ROI (+£13) and full coverage (415 races), and it already
incorporates the corrected as-of-date proxy that lets it predict horses
lacking a real TSR. Per the PRD, accuracy is the reliable signal and ROI is
noisier — so the choice is anchored on accuracy.

Alternatives considered:

- `RatingsXGBoostUngatedAlgorithm` (0.296 / +£19, 415 races) — closely
  behind, simpler model. The natural fallback if the proxy were dropped.
- `RidgeRegressionAlgorithm` (0.270 / +£129) — best ROI but lowest ML
  accuracy; its ROI is driven by occasional longshot wins and is the noisiest
  signal in the table.

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
- **Filters**: `KnownHorseAndJockey`, every horse predictable (all
  `PREDICTORS` non-null), field size ≤ 10. The TSR-gated variant additionally
  requires every horse in the race to have a non-null
  `LastRaceTopSpeedRating`.
- **Production-anchor command**: all 2026 `PredictionScores_*.csv` files,
  rows with `ResultStatus == 'CompletedRace'`, `accuracy = mean(FinishingPosition == 1)`,
  `roi = Σ DecimalOdds of winners − number of bets` (matching the eval).
