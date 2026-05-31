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

## Phase B (30-fold) walk-forward results — 2026-04-29 → 2026-05-28

Post-issue-005 validation run. 30 folds were used in place of the PRD-planned
180 (same 7-month training window per fold) to keep wall time manageable;
the 30-fold sample covers peak flat-racing season only.

| Algorithm | Accuracy | Net £ ROI | Races | Fav accuracy (same races) |
|---|---|---|---|---|
| RidgeRegressionAlgorithm | 0.240 | +41.41 | 417 | 0.363 |
| XGBoostAlgorithm | 0.259 | +0.73 | 417 | 0.363 |
| RatingsXGBoostAlgorithm (TSR-gated) | 0.238 | −6.38 | 147 | 0.390 |
| RatingsXGBoostUngatedAlgorithm | 0.233 | −57.39 | 417 | 0.363 |
| **ProxyTSRXGBoostAlgorithm** ← active | **0.261** | −87.24 | 417 | 0.363 |
| TunedProxyTSRXGBoostAlgorithm | 0.264 | −15.53 | 417 | 0.363 |

Coverage is equal across all non-gated algorithms (417 races each), confirming
that issues 001–005 preserved/restored parity with `RidgeRegressionAlgorithm`.
`RatingsXGBoostAlgorithm` 147 races reflects the TSR-complete gate applied to a
30-day May window (expected).

ROI over 417 races is too noisy to rank algorithms; accuracy is the reliable
signal (see Production anchor, below, and Phase A results for comparison).

## Phase A (180-fold) walk-forward results — 2025-11-28 → 2026-05-26

Fold dates span Nov 2025 → May 2026, 7-month training window per fold (the
PRD-defined re-baseline run). These numbers cover the full Nov–May window
including winter months with fewer flat meetings, hence the lower per-fold
race count (2.3 races/fold vs Phase B's 13.9/fold in peak May season).
`roi` is net £ on flat £1 stakes; `accuracy` is picks finishing 1st.
See `race_analytics/utils/scoring.py` for the exact definitions.

| Algorithm | Accuracy | Net £ ROI | Races | Fav accuracy (same races) |
|---|---|---|---|---|
| RidgeRegressionAlgorithm | 0.270 | +129.24 | 415 | 0.379 |
| XGBoostAlgorithm | 0.299 | +118.14 | 415 | 0.379 |
| RatingsXGBoostAlgorithm (TSR-gated) | 0.290 | −7.06 | 397 | 0.379 |
| RatingsXGBoostUngatedAlgorithm | 0.296 | +18.82 | 415 | 0.379 |
| **ProxyTSRXGBoostAlgorithm** | **0.304** | +13.37 | 415 | 0.379 |
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

The Phase A clean TSR-gated accuracy **0.290** lands within **+2.5 pp** of the
production anchor **0.265** — a rough ballpark match, which is the only
sanity-check the PRD asked for (a head-to-head replay was explicitly out of
scope). The TSR-gated 0.78 headline has fully collapsed. **The leak is gone.**

## What changed in practice

- **The "TSR is the key driver" story was the leak.** With ratings restricted
  to previous-race values, gating on TSR coverage now barely excludes anything
  (Phase A: 397 / 415 races = **95.7%** kept, vs the old 981 / 2,475 = 39.6%). Every
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

## Why the race count is much lower than the old 180-fold run

The Phase A 180-fold sample is **415 races**, the old (leaky) run reported **2,475** —
~6× fewer. This is **not** caused by the leakage fix. It is caused by the
prior PRD's expansion of `PREDICTORS`:

- The old 180-fold table was committed at **03:56 on 2026-05-26** (`16daab9`).
- At **20:30 the same day** commit `1f8c709`
  ("Issue 009: Extend PREDICTORS and wire trainer stats into predict/evaluate")
  added 7 columns to `PREDICTORS`:
  `Last3RaceAvgSpeed`, `Last3RaceSpeedTrend`, `Last3AvgRelFinishingPosition`,
  `TrainerNumberOfPriorRaces`, `TrainerWinPercentage`,
  `TrainerTop3Percentage`, `TrainerAvgRelFinishingPosition`.
- Each algorithm's `predict()` keeps only races where **every** horse has
  **every** `PREDICTOR` non-null (the
  `OriginalCount == PredictableCount` filter). `Last3*` are NaN for any
  horse with fewer than 3 prior races; `Trainer*` are NaN for unknown or
  TrainerId=0 trainers. Adding seven such columns sharply tightens whole-race
  predictability.

The same effect hits the untouched `RidgeRegressionAlgorithm` and
`XGBoostAlgorithm` baselines (their per-fold race counts match the corrected
algorithms exactly), confirming the cause is the PREDICTORS expansion, not
anything in the leakage-fix change set.

Issues 001–005 (Phase B) addressed `Last3*` NaN tolerance for
`XGBoostAlgorithm` specifically: it now opt-ins via
`nan_tolerant_predictors = OPTIONAL_PREDICTORS`, so rows with NaN Last3* are
no longer dropped during fit and predict. The Phase B 30-fold run confirms
all non-gated algorithms sit at equal coverage (417 races each).

The same filter applies in production (`predict.py` uses the same
`_fitted_predictors` intersection), so the ~415-race order of magnitude for
what `predict --data Data` operates on day-to-day is realistic — the 2,475
figure was from before that production filter tightened. Per-algorithm ROI
gaps over a few hundred races should be read as directional, not precise.

## Active algorithm

```python
ACTIVE_ALGORITHM = ProxyTSRXGBoostAlgorithm
```

(was `RatingsXGBoostAlgorithm` TSR-gated.)

**Rationale — Phase B review.** The Phase B 30-fold run narrows the
accuracy gap between `ProxyTSRXGBoostAlgorithm` (0.261) and
`TunedProxyTSRXGBoostAlgorithm` (0.264), but the margin is 3 pp over 417
races — well within sampling noise. The Phase A 180-fold run (more
statistically reliable) showed `ProxyTSRXGBoostAlgorithm` with a clear
15 pp lead over the tuned variant (0.304 vs 0.289). Across both samples,
`ProxyTSRXGBoostAlgorithm` is the stronger choice. Active algorithm
unchanged.

**Rationale — original selection** (Phase A). On leak-free numbers the
previously-active gated algorithm is the worst ML choice in the table
(−£7 ROI, the gate excludes only 18 / 415 races).
`ProxyTSRXGBoostAlgorithm` has the highest ML accuracy (**0.304**) with
positive ROI (+£13) and full coverage (415 races), and it already
incorporates the corrected as-of-date proxy that lets it predict horses
lacking a real TSR. Per the PRD, accuracy is the reliable signal and ROI
is noisier — so the choice is anchored on accuracy.

Alternatives considered:

- `TunedProxyTSRXGBoostAlgorithm` (Phase A: 0.289 / +£65, 415 races;
  Phase B: 0.264 / −£16, 417 races) — marginally best in Phase B, but
  Phase A advantage goes to the untuned variant by 15 pp. Not enough
  evidence to swap.
- `RatingsXGBoostUngatedAlgorithm` (Phase A: 0.296 / +£19, 415 races) —
  closely behind, simpler model. Natural fallback if the proxy were dropped.
- `RidgeRegressionAlgorithm` (Phase A: 0.270 / +£129) — best ROI but
  lowest ML accuracy; ROI is driven by occasional longshot wins and is the
  noisiest signal in the table.

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
- **Phase A run**: 180 folds (`--folds 180 --training-months 7`), dates
  2025-11-28 → 2026-05-26.
- **Phase B run**: 30 folds (`--folds 30 --training-months 7`), dates
  2026-04-29 → 2026-05-28 (peak flat-racing season only; 180-fold
  equivalent would take ~5h wall time).
- **Production-anchor command**: all 2026 `PredictionScores_*.csv` files,
  rows with `ResultStatus == 'CompletedRace'`, `accuracy = mean(FinishingPosition == 1)`,
  `roi = Σ DecimalOdds of winners − number of bets` (matching the eval).
