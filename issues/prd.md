# PRD: Remove post-race rating leakage from the ratings algorithms

## Problem Statement

I rely on `RatingsXGBoostAlgorithm` (and the `ProxyTSR` variants) to pick winners in
`TodaysPredictions.csv`. The walk-forward evaluation tells me these algorithms are
excellent — the TSR-gated `RatingsXGBoostAlgorithm` reports up to **0.78 accuracy** and
huge positive ROI in `evaluations.md`. But the predictions I actually get in production are
nowhere near that good, and I strongly suspected the evaluation was flattering itself.

The exploration confirmed it. The features `RacingPostRating` (RPR) and `TopSpeedRating`
(TSR) stored in the `Results_*.csv` files are **post-race performance figures** — Racing
Post assigns them *from the run itself*. Within a single race they reproduce the finishing
order almost perfectly:

| Rating | Within-race Spearman vs finishing position | Top-rated horse wins |
|---|---|---|
| `OfficialRating` | −0.11 (genuine pre-race mark) | 18.7% |
| `RacingPostRating` | **−0.88** (post-race) | 74.3% |
| `TopSpeedRating` | **−0.86** (post-race) | 70.8% |

Because `Horse_Stats.csv` carries no rating columns, these ratings reach the model **only
through the race-day row**:

- In `evaluate.py`, the fold's race card is built from that day's **results rows**, so the
  model is handed near-oracle RPR/TSR — it is effectively told the answer.
- In `predict.py`, the card (`TodaysRaceCards.csv`) carries only the weak **pre-race form**
  RPR/TSR (and TSR is only ~57% populated).

The result is a train/serve skew that massively inflates evaluation. The recorded
production predictions prove the gap: across the 2026 `PredictionScores_*.csv` logs (514
completed bets) the **real accuracy was 0.265**, versus the **0.78** the evaluation claimed
for the same gated strategy — roughly **3× inflation**.

`ProxyTSRXGBoostAlgorithm` has the same primary leak (it still feeds raw RPR/TSR) plus a
second, temporal one: its per-horse `PeakProxyTSR/LastProxyTSR/Best5ProxyTSR` are
aggregated over the whole training window, so a training row can see that horse's *future*
races.

## Solution

Make every rating feature a **previous-race** value — the rating the horse earned in its
last completed race — computed identically in training and serving, so the model never sees
information that would not exist before a race is run. Then re-evaluate the algorithms
honestly and re-baseline `evaluations.md`.

Concretely:

- All three ratings become `LastRace{Official,RacingPost,TopSpeed}Rating`. These already
  exist in `Race_Features.csv` (computed strictly from prior days, so leak-free) and will be
  plumbed into `Horse_Stats.csv` for serving. Both algorithms read every rating from the
  per-horse stats join — **nothing rating-related comes from the race card any more**.
- The `ProxyTSR` approach is fixed in place: drop the raw RPR/TSR from its features and make
  the proxy an as-of-date "last prior proxy" per horse instead of a whole-window aggregate,
  with the proxy regressor trained only on the fold's training data.
- The `require_tsr` gate is redefined on **previous-race** TSR coverage (all horses have a
  clean `LastRaceTopSpeedRating`), keeping a gated and an ungated variant for comparison.
- Re-run the 180-fold walk-forward evaluation, characterise the true performance against all
  baselines, and sanity-check that the cleaned gated-strategy accuracy lands near the ~0.265
  production anchor. Then decide which algorithm (if any) should be `ACTIVE_ALGORITHM`.

The expectation is set up front: accuracy will fall sharply (likely ~0.25–0.30) and the
"TSR is the key driver" / TSR-gated headline in `evaluations.md` will collapse. Previous-race
ratings should still be a genuine horse-quality signal that beats `LastRaceSpeed`.

## User Stories

1. As a punter using `TodaysPredictions.csv`, I want the algorithm to be trained and
   evaluated only on information that exists before a race is run, so that the predictions I
   get in production behave like the evaluation says they will.
2. As a punter, I want the evaluation accuracy and ROI to be honest estimates of real-world
   performance, so that I can trust them when deciding how much to stake.
3. As a developer, I want `RacingPostRating` and `TopSpeedRating` replaced by the horse's
   previous-race RPR/TSR, so that the model uses a genuine quality signal rather than a
   post-race readout of the result.
4. As a developer, I want `OfficialRating` to also use the previous-race value, so that all
   three ratings share one consistent "last completed race" definition.
5. As a developer, I want the previous-race rating features computed identically in the
   training pipeline and the serving path, so that there is no train/serve skew.
6. As a developer, I want `Horse_Stats.csv` to carry `LastRaceOfficialRating`,
   `LastRaceRacingPostRating` and `LastRaceTopSpeedRating`, so that `predict()` can source
   ratings from the per-horse stats join instead of the race card.
7. As a developer, I want both `RatingsXGBoostAlgorithm` and its ungated variant to read all
   ratings (absolute and field-relative) from the previous-race columns, so that no rating
   enters the model from the current race.
8. As a developer, I want the field-relative rating features (`Rel*`) recomputed from the
   previous-race ratings, so that the relative signal is also leak-free.
9. As a developer, I want the `require_tsr` gate redefined on previous-race
   `LastRaceTopSpeedRating` coverage, so that gating reflects clean data availability rather
   than selecting the highest-leak races.
10. As a developer, I want to keep a gated and an ungated `RatingsXGBoost` variant, so that I
    can compare whether concentrating on horses with richer history improves ROI per race.
11. As a developer, I want `ProxyTSRXGBoostAlgorithm` to stop feeding raw current-race RPR
    and TSR as features, so that it no longer inherits the primary leak.
12. As a developer, I want the proxy TSR turned into an as-of-date per-horse value (the
    horse's last prior proxy) instead of a whole-window peak/last/best5 aggregate, so that a
    training row cannot see that horse's future races.
13. As a developer, I want the `ProxyTSRModel` regressor fitted only on the fold's training
    data during evaluation, so that fold-day TSR labels never leak into the proxy.
14. As a developer, I want `TunedProxyTSRXGBoostAlgorithm` to keep working on the corrected
    proxy, so that the tuned variant remains comparable.
15. As a developer, I want the card's rating columns removed from the prediction/evaluation
    card builders once they are unused, so that the only rating source is the per-horse
    stats join and the data flow is unambiguous.
16. As a developer, I want the 180-fold walk-forward evaluation re-run on the corrected
    algorithms against the market-favourite, ridge and xgboost baselines, so that I get a
    leak-free comparison across a statistically meaningful window.
17. As a punter, I want the cleaned gated-strategy evaluation accuracy compared against the
    ~0.265 real production anchor from the `PredictionScores_*.csv` logs, so that I have
    evidence the leak is actually gone.
18. As a developer, I want `evaluations.md` to carry a prominent leakage warning immediately,
    so that nobody trusts the inflated numbers while the fix is in progress.
19. As a developer, I want `evaluations.md` rewritten with the corrected numbers once the
    re-evaluation completes, so that the document reflects honest performance.
20. As a developer, I want `ACTIVE_ALGORITHM` reviewed after the re-evaluation, so that the
    production predictor is chosen on the basis of leak-free results.
21. As a developer, I want the changed feature builders and algorithms covered by behaviour
    tests that mirror the existing test suite, so that the previous-race-rating and
    as-of-date-proxy behaviour is pinned against regression.
22. As a developer, I want the `run.ps1` flow to keep working unchanged (build features →
    predict), so that the next pipeline run regenerates `Horse_Stats.csv` with the new
    columns and predicts from them automatically.

## Implementation Decisions

### Rating features become previous-race values

- All three ratings used by the ratings algorithms switch from the current race's
  `OfficialRating`/`RacingPostRating`/`TopSpeedRating` to the horse's last completed race
  values: `LastRaceOfficialRating`, `LastRaceRacingPostRating`, `LastRaceTopSpeedRating`.
- `CalculateHorsesStats` already produces all three `LastRace*` rating columns in
  `Race_Features.csv`, computed from strictly prior days (`history < slice_start`), so the
  training-side values are already leak-free and require no change to the processor.
- `extract_horse_stats` is extended to carry the three `LastRace*` rating columns into
  `Horse_Stats.csv`, mirroring the existing pattern that renames the most-recent race's raw
  columns (e.g. `Speed → LastRaceSpeed`). For serving, the most-recent completed race's
  `OfficialRating/RacingPostRating/TopSpeedRating` become the `LastRace*` rating values for
  today — consistent in meaning with the training definition.

### `RatingsXGBoostAlgorithm` (and ungated variant)

- The feature set replaces the current-race rating columns and their `Rel*` derivatives with
  the `LastRace*` rating columns and `Rel*` derivatives computed from them (field-relative =
  value minus the race-mean of that previous-race rating).
- `predict()` sources the rating features from the `horse_stats` merge rather than from the
  `races` card argument. No rating column is read from the card.
- The `require_tsr` gate is redefined to require every horse in a race to have a non-null
  `LastRaceTopSpeedRating`. The gated and ungated variants are both retained as registered
  algorithms for comparison.

### `ProxyTSRModel` and `ProxyTSRXGBoostAlgorithm`

- The proxy stays self-contained inside the algorithm. `ProxyTSRModel` continues to be fitted
  only on the (training) rows that have a real `TopSpeedRating`; during evaluation this is the
  fold's training data, so no fold-day labels leak into the regressor.
- The regressor emits a per-race proxy TSR. The algorithm then derives an as-of-date
  per-horse value (the horse's last prior proxy) rather than the current whole-window
  `PeakProxyTSR/LastProxyTSR/Best5ProxyTSR` aggregate, eliminating the temporal leak.
- The raw current-race `RacingPostRating`/`TopSpeedRating` are removed from the proxy
  algorithm's feature set; it uses the same previous-race rating features as
  `RatingsXGBoostAlgorithm`, plus its as-of-date proxy feature(s).
- `TunedProxyTSRXGBoostAlgorithm` inherits the corrected behaviour.

### Card builders / data flow

- Because ratings now flow exclusively through the per-horse stats join, the rating columns
  in the prediction and evaluation card builders (the `RaceCard`/`_race_card` column lists)
  become unused and are trimmed so the data flow is unambiguous.
- No CSV schema change to the append-only monthly `Results_*.csv` files. The schema change is
  additive: `Horse_Stats.csv` gains `LastRaceOfficialRating`, `LastRaceRacingPostRating` and
  `LastRaceTopSpeedRating`. `Race_Features.csv` already contains these columns.

### Re-evaluation and re-baselining

- Re-run the walk-forward evaluation at 180 folds on the corrected algorithms against the
  market-favourite, ridge-regression and xgboost baselines. No hard pass/fail bar — the goal
  is an honest characterisation (accuracy, ROI, coverage, field-size breakdowns).
- Compute the real production accuracy/ROI from the `PredictionScores_*.csv` logs (~0.265
  accuracy) and sanity-check that the cleaned gated-strategy evaluation lands in the same
  ballpark.
- After re-evaluation, review `ACTIVE_ALGORITHM` and update it if the evidence supports a
  different choice.

### Documentation

- `evaluations.md` gets a prominent leakage warning at the top immediately (the existing
  numbers are inflated by post-race RPR/TSR leakage; real accuracy ~0.265), then is rewritten
  with the corrected numbers once the clean 180-fold re-evaluation completes.

### Pipeline wiring

- `run.ps1` is unchanged. Its existing `build_features → predict` sequence regenerates
  `Horse_Stats.csv` with the new columns and serves predictions from them on the next run.

## Testing Decisions

- **What makes a good test here:** assert on externally observable behaviour, not internals.
  For feature builders, drive the public functions and assert on the resulting DataFrame
  columns/values. For algorithms, drive `fit()`/`predict()` on small synthetic frames and
  assert on the selected feature columns and the predicted output, following the existing
  suite's style.
- **Modules to test (behaviour tests, mirroring prior art):**
  - `extract_horse_stats` — extends `tests/features/test_horse_stats.py` to assert the three
    `LastRace*` rating columns are present in the output and equal the horse's most-recent
    completed race ratings.
  - `RatingsXGBoostAlgorithm` / ungated variant — extends `tests/algorithms/test_predictors.py`
    (or a dedicated test) to assert the fitted feature set uses the `LastRace*` rating columns
    and contains no current-race rating column, and that `predict()` reads ratings from the
    `horse_stats` argument (not the card). Include a gate test on `LastRaceTopSpeedRating`
    coverage.
  - `ProxyTSRModel` / `ProxyTSRXGBoostAlgorithm` — extends `tests/algorithms/test_proxy_tsr.py`
    and `tests/algorithms/test_proxy_tsr_xgboost.py` to assert the proxy value for a training
    row depends only on that horse's prior races (an added future race does not change it) and
    that raw RPR/TSR are absent from the feature set.
- **Prior art:** the existing pytest suite under `tests/` mirroring `race_analytics/`
  (e.g. `test_horse_stats.py`, `test_proxy_tsr_xgboost.py`, `test_predictors.py`,
  `test_evaluate.py`). New tests follow the same fixtures/style.
- **No dedicated leakage-detection guardrail** (no within-race-correlation scan and no
  standalone "leak guard" test) — explicitly out of scope per decision; correctness is
  protected by the behaviour tests above plus review.
- The 180-fold re-evaluation and the `PredictionScores` anchor comparison are verification
  activities (run via the evaluate script / one-off analysis), not automated tests.

## Out of Scope

- Any change to the C# extraction stage (`RacePredictor.Core`, `RaceDataDownloader`) or to
  how ratings are scraped. The fix is entirely in the Python ML stage.
- Changing the schema of the append-only monthly `Results_*.csv` files.
- A generic leakage-detection guardrail (within-race correlation scan or standalone guard
  test).
- A matched backtest replaying the exact dates/races in the `PredictionScores_*.csv` logs
  (we use a rough sanity match against the ~0.265 anchor, not a head-to-head replay).
- Hyperparameter re-tuning of the corrected models beyond what already exists
  (`TunedProxyTSRXGBoostAlgorithm` is kept, but no new search is required by this PRD).
- Changing `RidgeRegressionAlgorithm` or `XGBoostAlgorithm` (they do not use ratings and
  serve as clean baselines).

## Further Notes

- **Expect the numbers to fall.** Accuracy is likely to land around 0.25–0.30 and the
  TSR-gated headline (0.60–0.78 accuracy, large ROI) will collapse, because that result was
  the model reading the finishing order off the post-race TSR/RPR columns. This is the
  intended outcome, not a regression.
- **The previous-race ratings should still help.** A horse's last earned RPR/TSR is a genuine
  pre-race quality signal and is expected to beat `LastRaceSpeed`, so the cleaned model should
  remain a sensible predictor even if it no longer beats the market favourite.
- **Reality anchor for reference:** across the 2026 `PredictionScores_*.csv` logs (514
  completed bets), the production picks hit 0.265 accuracy with positive flat-stake ROI in
  that sample; the accuracy is the reliable signal, the ROI is noisier.
- **Coverage after the fix:** with previous-race TSR, the gated variant gates on real
  `LastRaceTopSpeedRating` coverage; once the proxy is fixed, nearly every horse with a prior
  race has a proxy value, so a proxy-coverage gate would rarely exclude anything — the
  meaningful gate is real `LastRaceTopSpeedRating`.
- **Sequencing:** this PRD will be broken into vertical-slice issues (`issues/NNN-*.md`) via
  the prd-to-issues workflow and implemented TDD-first.
