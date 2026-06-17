# PRD: Odds-aware features via `MarketProb` (forecast odds, SP placeholder)

## Problem Statement

The pipeline now captures a real pre-race **forecast** price (the Racing Post morning
"tissue") for every runner. On `TodaysRaceCards.csv` it lands in `DecimalOdds`/
`FractionalOdds` at download; in `Results_*.csv` the `validate` step copies it into the
new optional `ForecastDecimalOdds`/`ForecastFractionalOdds` columns (forward-only, no
backfill — so historic results carry none yet).

To date the algorithms have been forbidden from using any odds at all: the long-standing
leakage rule (`docs/data-pitfalls.md`, Pitfall 2) bars odds from being a model feature or
a selection/filter. That rule was written when the only odds available were the post-race
SP and a `"SP"` placeholder on the card. Now that a genuine **pre-race** price exists at
prediction time, the market's own view of each horse's chance — by far the strongest
signal in the data (the market favourite wins ~38.5% of races, against the models' ~30%) —
is being deliberately thrown away.

We want the algorithms to be *able* to use this market signal, evaluated honestly, without
silently re-importing the leakage the rule exists to prevent, and without prematurely
shipping a model trained on a stand-in that overstates its real-world edge.

## Solution

Introduce a single market-derived feature, **`MarketProb`** — the normalized
market-implied win probability — and make it available to every algorithm as an optional
predictor. The value is sourced from the forecast price wherever it exists and falls back
to the existing SP column otherwise, through one shared resolver, so the code prefers the
forecast automatically and the SP fallback is a transitional placeholder that retires
itself as coverage accrues.

Because there is essentially **zero** forecast coverage in history today, any evaluation we
run now is measuring the SP placeholder, not the forecast feature the model will actually
serve on in production. We therefore treat this work as **plumbing plus a diagnostic
A/B**: every algorithm gains the feature, we re-run the full walk-forward comparison to see
how each responds, and we record the results — but we do **not** change the production
`ACTIVE_ALGORITHM` off these numbers. A reminder is scheduled to re-evaluate once real
forecast coverage exists, at which point adoption is reconsidered against the normal gate.

This deliberately and explicitly crosses "bar 2" of the leakage rule for the forecast
price (a value that is genuinely knowable before the race) while keeping the discipline
intact for the post-race SP, and the guardrail docs are updated to say so.

## User Stories

1. As a model developer, I want each runner's market-implied win probability available as
   an optional model feature, so that algorithms can learn from the strongest signal in the
   data.
2. As a model developer, I want that feature derived from the forecast price when it exists
   and the SP price when it doesn't, through one resolver, so that the source of truth is
   defined in exactly one place.
3. As a model developer, I want the resolver to prefer the forecast automatically, so that
   the SP placeholder retires itself as forecast coverage accrues, with no later code change.
4. As a model developer, I want `MarketProb` normalized within each race so the field sums
   to 1, so that the bookmaker overround is removed and the value is a true probability
   comparable to the model's own `WinProbability`.
5. As a model developer, I want missing or void odds to resolve to a uniform prior
   (1 / field size) rather than NaN, so that the column stays dense and the linear models
   (e.g. Ridge) do not break.
6. As a model developer, I want `MarketProb` added to the shared optional-predictor list,
   so that the win-classifier family and the regressor family all pick it up without
   per-algorithm wiring.
7. As a model developer, I want the feature materialized identically on the training path
   and the serving path, so that what a model trains on matches what it predicts on.
8. As a punter, I want production predictions to use the morning forecast price (already on
   the card) for `MarketProb`, so that the served feature reflects a price I could actually
   bet at.
9. As an evaluator, I want the full walk-forward evaluation to source odds from the new
   field with SP fallback, so that the eval honours the same resolution rule as the model.
10. As an evaluator, I want race selection left unchanged (known horse and jockey, every
    runner predictable, field size ≤ 10), so that adding the feature does not silently
    shrink or shift the evaluated population.
11. As an evaluator, I want ROI to value winning bets at the resolved odds (forecast → SP),
    so that reported returns reflect the price actually available at prediction time as
    forecast coverage grows.
12. As an evaluator, I want the market-favourite baseline to pick the morning favourite by
    resolved odds, so that the baseline and the feature use a consistent notion of "the
    market".
13. As an evaluator, I want `MarketProb` (and the resolved odds) logged in the evaluation
    output CSV, so that I can analyse how strongly each algorithm leans on the market signal.
14. As an evaluator, I want the full A/B re-run across every registered algorithm, so that I
    can see each algorithm's distinct response to the new feature rather than just one
    variant's.
15. As a maintainer, I want the eval results recorded in `evaluations.md` under a clearly
    flagged "SP-placeholder / diagnostic" section, so that nobody later mistakes them for
    decision-grade forecast results.
16. As a maintainer, I want the production `ACTIVE_ALGORITHM` left untouched by this work,
    so that no model trained on the SP placeholder reaches production by accident.
17. As a maintainer, I want a reminder scheduled to re-evaluate once forecast coverage is
    meaningful, so that adoption is reconsidered on honest data and not forgotten.
18. As a future maintainer, I want the leakage guardrails (`docs/data-pitfalls.md`,
    `docs/odds-capture.md`, and the relevant memory note) updated to record that odds are
    now a deliberately sanctioned feature with a forecast-vs-SP caveat, so that the docs do
    not contradict the code.
19. As a future maintainer, I want the known divergence between the SP-placeholder eval and
    the forecast-fed production behaviour documented, so that the accuracy jump we expect is
    understood as "following the favourite", not as a genuine edge.
20. As a future maintainer, I want the PRD to state that a fully forecast-fed training
    window will not exist for months, so that the re-eval threshold is chosen with that
    reality in mind rather than a hard-coded date.

## Implementation Decisions

- **One odds resolver / `MarketProb` helper.** A single pure function owns the rule:
  resolve a runner's decimal odds as forecast-when-present-else-SP, convert to implied
  probability (1 / decimal), normalize within the race so the field sums to 1, and fall
  back to a uniform prior (1 / field size) when odds are missing or the runner is
  void/non-completing. This is the only place the coalesce and the normalization live.
- **Materialize in two non-shared places.** The training frame built in the evaluation
  harness does not re-run the canonical serving transform chain, so `MarketProb` must be
  produced in both: (a) the harness's in-memory feature-engineering step, which must also
  start carrying `ForecastDecimalOdds` alongside the existing `DecimalOdds`; and (b) a new
  `calculate_market_prob` transform appended to the canonical transform chain in the
  `RaceData` builder, which covers eval serving and production serving through one code
  path. Both call the shared helper.
- **Odds columns must survive into the card subsets.** The serving-card column selections
  (production card columns and the eval `race_card` projection) must retain the decimal
  odds column(s) so the transform can compute `MarketProb` at serve time. On the live card
  the morning forecast already occupies `DecimalOdds`, so production naturally serves the
  forecast-derived value with no SP involved.
- **Feature exposed via the shared optional-predictor list.** `MarketProb` is added to the
  shared `OPTIONAL_PREDICTORS` set so the win-classifier family and the regressor family
  pick it up through their common feature-universe selection. The regressor path will be
  verified to actually include it; linear models are protected by the uniform-prior
  imputation (no NaN reaches the estimator).
- **No new within-race `Rel` companion required.** `MarketProb` is already normalized
  within the race, so the relativity it would otherwise need is built in; a separate
  `Rel`-companion is not added unless a later evaluation shows it helps.
- **Race selection unchanged.** No odds-presence gate is introduced. The predicted
  population stays exactly as today.
- **Measurement sourced through the same resolver.** ROI valuation values winners at the
  resolved odds (forecast → SP), and the market-favourite baseline selects by resolved
  odds. Under the stated forecast ≈ SP assumption this is a no-op on historic data and only
  begins to diverge as forecast coverage accrues.
- **Diagnostic logging.** The evaluation results CSV gains `MarketProb` (and the resolved
  odds) per predicted runner so the feature's influence can be inspected post-hoc.
- **Adoption is gated on honest data, not this run.** The full A/B is run across all
  registered algorithms and recorded as diagnostic. `ACTIVE_ALGORITHM` is not changed. A
  reminder is scheduled (threshold chosen later, deliberately not a hard-coded date) to
  re-run once `ForecastDecimalOdds` coverage is meaningful, and adoption is reconsidered
  then against the existing gate (ROI and early/late stability).
- **Guardrail docs and memory updated.** Pitfall 2 in the data-pitfalls doc, the
  leakage-guardrail note in the odds-capture doc, and the odds memory note are revised to
  state that `MarketProb` is a sanctioned, deliberate feature, that the SP fallback is a
  transitional placeholder, and that the post-race SP remains barred as a *direct* feature.

## Testing Decisions

- **Python is the gap.** Every module this PRD touches is on the Python ML side, which has
  little to no automated test coverage today. This PRD treats that as the primary testing
  opportunity rather than relying solely on `.\run.ps1` output.
- **Extract pure functions and unit-test them.** The odds resolver / `MarketProb` helper is
  a pure function over a race frame and is the highest-value unit under test. Cover:
  forecast-present uses forecast; forecast-absent falls back to SP; per-race normalization
  sums to 1; missing/void odds resolve to the uniform prior; a full-field example produces
  the expected probabilities. The new `calculate_market_prob` transform is tested for
  producing the column on both a Results-shaped frame (with the forecast column) and a
  card-shaped frame (forecast in `DecimalOdds` only).
- **Test the train/serve parity explicitly.** A test asserts that a runner's `MarketProb`
  is computed the same way whether it arrives via the harness training path or via the
  canonical serving transform, so the documented two-place materialization cannot silently
  drift.
- **Test the measurement change in isolation.** ROI valuation and the favourite baseline
  are tested against small synthetic frames to confirm: forecast-present values at forecast,
  forecast-absent values at SP, and that historic SP-only data is unchanged.
- **Behavioural, not implementation, assertions.** Tests assert on the resolved frame /
  scores produced, not on internal call structure. Larger end-to-end confidence still comes
  from a short walk-forward eval invocation (small folds) and a single `predict` run on a
  card, but those are smoke checks, not the primary safety net.
- **No new C# behaviour is under test here** — the forecast columns and the `validate`
  merge already ship with their own coverage. This PRD does not change the C# stage.

## Out of Scope

- **Capturing live / market odds (Phase 2).** This PRD uses only the already-captured
  forecast price. The live in-running market remains uncaptured and is explicitly deferred.
- **Changing the production active algorithm.** No promotion happens off the SP-placeholder
  eval; adoption is a later decision on forecast-fed data.
- **Adding an odds-presence race-selection gate.** Selection criteria are unchanged.
- **Backfilling forecast odds into historic results.** The merge is forward-only by design;
  no historic backfill is attempted.
- **Value-betting / market-overlay strategies** (bet only when model probability exceeds
  market-implied probability, staking by edge, etc.). These depend on a trustworthy live
  price and are out of scope.
- **Choosing the exact re-eval date or coverage threshold.** The PRD commits to scheduling
  a reminder, not to a specific date.
- **Any change to the post-race SP's status as a direct feature** — it stays barred; only
  the resolver's transitional fallback uses it.

## Further Notes

- **Why this is allowed now.** The leakage rule has two bars: (1) was the value knowable
  before the race, and (2) is feeding it deliberate and safe. The forecast price clears
  bar 1 (it exists at download). This PRD consciously clears bar 2 for the forecast price by
  introducing it deliberately, behind a resolver, with honest evaluation and deferred
  adoption.
- **Known risk — eval/production divergence.** With near-zero forecast coverage, the eval
  trains *and* serves on SP, while production will serve on the weaker morning forecast.
  This is the exact failure shape that once inflated a ratings model from a real ~0.265 to a
  reported 0.78. The mitigation is structural: this eval is diagnostic-only and cannot move
  `ACTIVE_ALGORITHM`.
- **Known risk — within-window drift for the recency-weighted active model.** Once forecast
  begins to populate, the same column means SP for old rows and forecast for new rows. The
  current active algorithm weights the newest rows most heavily (~70-day half-life), which
  is precisely where the forecast/SP transition first appears — so its behaviour is the most
  sensitive to the mixed window. Worth watching at re-eval time.
- **Expect an accuracy jump, and read it correctly.** Because the market signal is so
  strong, the win-classifiers are likely to lean on it heavily and drift toward "pick the
  favourite". In this eval that favourite is defined by SP, so the jump reflects following
  a sharp post-window price, not a genuine forecast-time edge.
- **A fully forecast-fed window is months away.** A 7-month training window made entirely of
  forecast-covered rows will not exist for ~7 months. A ~1-month-coverage checkpoint is
  still roughly six-sevenths SP — a useful early read, not a clean one. The re-eval reminder
  should be set with that in mind.
