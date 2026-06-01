# PRD: ROI-driven improvement via abstain-filtering and new pre-race features

## Problem Statement

As a punter, the active prediction model (`ProxyTSRXGBoostAlgorithm`) bets one horse in
*every* predictable race and loses money doing it. Over the 180-fold walk-forward window it
picks the winner 29.4% of the time and returns **−£22** on flat £1 stakes across 2,517 bets —
and on those same races, simply backing the market favourite would have won 38.5% and returned
**+£44**. The model bets indiscriminately: it has no notion of how confident it is on a given
race, nor whether a race is inherently a coin-flip (huge-field handicap sprints, etc.). I would
rather bet *fewer* races for a *better* return than keep betting everything at a loss — provided
I'm still given predictions on a reasonable share of races.

Two further realities constrain any fix:

- **Market odds are not available when predictions are made.** On the downloaded racecard,
  `DecimalOdds` is empty and `FractionalOdds` is the literal string `"SP"`. So nothing that
  depends on the price — value/overlay betting, market-aware features, market-competitiveness
  filters — is deployable. Odds exist only retrospectively (the starting price in the results
  files) and can be used *only* to measure ROI after the fact.
- The previous ratings-leakage episode showed that an evaluation can flatter a model badly if
  any signal is computed from data not genuinely available before the race.

## Solution

Improve the *return on the races actually bet* through two complementary, independently-simple
changes, both validated by walk-forward re-evaluation against the current baseline:

1. **New pre-race features.** Wire in already-available, leak-free signals (race class, field
   size, draw, age, race-quality bands, surface/trip-change flags, and — in a second tier —
   course/going/distance-specific form) to sharpen the model, especially on the segments where
   the diagnostic shows it is weak.

2. **A two-gate abstain layer.** Bet a race only if it passes **both** of:
   - **Filter A — confidence gate:** the model is sufficiently sure (high top-pick win
     probability and/or a clear gap to its second pick).
   - **Filter B — hard-race rules:** the race is not one of a short, approved list of
     inherently-hard race shapes.

   Coverage is kept at **≥50%** of currently-predictable races, and we choose the operating
   point from a ROI-vs-coverage frontier.

The work proceeds diagnose → implement → re-evaluate. A diagnostic first establishes *when* the
model wins and loses; that analysis nominates both the hard-race rules and the features worth
trying. Changes are adopted only if they beat the current baseline's ROI-vs-coverage frontier
at ≥50% coverage in a way that is stable across the window. No odds-derived signal enters the
model or the filters at any point.

## User Stories

1. As a punter, I want the model to skip races it isn't confident about, so that my flat-stake ROI on the races I do bet improves.
2. As a punter, I want the model to skip race shapes that are inherently hard to predict (e.g. very large handicaps), so I stop losing on near-coin-flips.
3. As a punter, I want predictions on at least half of the currently-predictable races, so abstaining doesn't leave me with almost nothing to bet.
4. As a punter, I want coverage (how many races were skipped) reported alongside accuracy and ROI, so I understand the trade-off I'm getting.
5. As a data scientist, I want a diagnostic that shows where the model wins and loses by segment (field size, class, race type, distance, going, age band, confidence band), so I know what to fix.
6. As a data scientist, I want per-horse win-probabilities persisted from evaluation, so I can measure model confidence and calibration.
7. As a data scientist, I want the model's confidence exposed as top-pick win-probability and gap-to-second-pick, so I can build a confidence-based abstain gate.
8. As a data scientist, I want both confidence metrics implemented and compared, so the one that produces the better ROI-vs-coverage frontier is the one we keep.
9. As a data scientist, I want a ROI-vs-coverage frontier across confidence thresholds, so I can pick an operating point that maximises ROI at ≥50% coverage.
10. As a data scientist, I want the abstain threshold derived from each fold's training data only, so the evaluation stays walk-forward-honest with no outcome leakage.
11. As a data scientist, I want candidate hard-race rules proposed from the diagnostic together with their out-of-sample effect, so I can approve only the sensible, stable ones.
12. As a data scientist, I want to approve a short list of 2–4 hard-race rules, so the filter stays simple and interpretable.
13. As a data scientist, I want race-level context columns (field size, class, …) persisted in the eval output, so segment analysis doesn't require re-joining the raw results each time.
14. As a modeller, I want `WeightChange` and `DistanceChange` wired into the feature set, so the trivial signals already computed in the codebase are actually used.
15. As a modeller, I want field size exposed as an explicit feature, so the model can account for race competitiveness.
16. As a modeller, I want race `Class` encoded as an ordinal feature, so race quality informs predictions.
17. As a modeller, I want horse age and race-relative age as features, so maturity within a field is captured.
18. As a modeller, I want draw features (draw percentile / relative draw) for flat races, so stall bias is captured where it matters and ignored where it doesn't.
19. As a modeller, I want race quality/eligibility one-hots (`Pattern`, `RatingBand`, `AgeBand`, `SexRestriction`), so race context informs predictions.
20. As a modeller, I want surface-switch and code-switch (flat ↔ jumps) flags, so horses stepping into unfamiliar conditions are flagged.
21. As a modeller, I want first-time/changed-headgear and same-jockey-as-last-run flags (second tier), so well-known form angles are available.
22. As a modeller, I want course-, going- and distance-specific prior-form aggregates (second tier), so a horse's record under today's conditions counts.
23. As a modeller, I want features screened quickly on the fast XGBoost model before any full ProxyTSR re-evaluation, so I don't spend ~1.7h per idea.
24. As a modeller, I want only the features that target the diagnosed weak segments tried first, so feature work stays focused.
25. As an evaluator, I want the new configuration compared to the current ProxyTSR baseline on the ROI-vs-coverage frontier, so adoption is evidence-based.
26. As an evaluator, I want any gain checked on an early-vs-late time split, so I don't adopt a lucky artifact of a few races.
27. As an evaluator, I want results sanity-checked against the 0.265 / +£78 production anchor, so the eval numbers stay believable.
28. As a maintainer, I want the abstain layer to ride through both evaluation and production prediction, so production actually abstains the same way evaluation does.
29. As a maintainer, I want the improved model registered as a new algorithm and promoted to the active algorithm only if it clears the acceptance bar, so production isn't changed on a whim.
30. As a maintainer, I want `evaluations.md` updated with honest frontier numbers and coverage, so the record reflects reality.
31. As a maintainer, I want no odds-derived input anywhere in the model or the filters, so the pipeline stays deployable when odds are absent pre-race.
32. As a developer, I want the confidence gate and the hard-race rules built as pure, separately-testable modules, so their logic is verified in isolation.
33. As a developer, I want the new feature transforms tested for NaN and structural-blank handling (draw null on jumps, blank class, "None" sex restriction), so missing data never breaks prediction.
34. As a developer, I want any conditioned-form aggregate to exclude the current race, so the second-tier features cannot leak.

## Implementation Decisions

**Objective and constraints**

- ROI is the primary objective; top-pick accuracy is treated as a lever for ROI, not the goal.
- Coverage must stay at **≥50%** of currently-predictable races (≈1,259 of 2,517).
- **No odds at decision time.** No model input, feature, filter, or selection rule may be
  derived from odds. Odds are used solely to compute ROI/accuracy retrospectively in evaluation.
- **Walk-forward discipline.** Every feature and filter is computed from training data strictly
  prior to the fold; abstain thresholds are derived from each fold's training window; nothing is
  fit to outcomes that are then reported. The full-window diagnostic is hypothesis-generation
  only.
- **Target model:** the active `ProxyTSRXGBoostAlgorithm`. The plain `XGBoostAlgorithm` is used
  as a fast screening proxy for feature selection (≈1 min for 180 folds vs ≈1.7h for ProxyTSR).
- **Acceptance bar:** adopt a change only if its ROI-vs-coverage frontier dominates the current
  ProxyTSR baseline at ≥50% coverage, the gain is stable on an early-vs-late split, and the
  numbers remain consistent with the production anchor.

**Modules built or modified**

- **Confidence gate** — a new pure module. Given a race's per-horse win-probabilities it
  computes the top-pick probability and the gap to the second pick and decides keep/abstain
  against a threshold. Both metrics are implemented; the frontier comparison selects which to
  keep. Thresholds are expressed as training-distribution coverage quantiles.
- **Hard-race rules** — a new pure module. Given race-card attributes (field size, class, race
  type, handicap flag inferred from `RatingBand` presence) it returns a skip boolean. The 2–4
  approved rules are applied uniformly to all folds.
- **Abstain wrapper algorithm** — a new algorithm class composing the hard-race rules and the
  confidence gate over `ProxyTSRXGBoostAlgorithm`, reusing the existing `_apply_gate` hook
  pattern in the binary-win-classifier base. Registered in the algorithm registry and a
  candidate for the active-algorithm marker. The two gates are independent (A reads the model's
  output, B reads the card) and a race is bet only if it passes both.
- **Per-horse probability exposure** — the binary-win-classifier algorithm is modified to make
  the full ranked field with its `WinProbability` available to callers (evaluation persistence
  and the confidence gate), while preserving the existing rank-1 selection semantics for the
  production pick.
- **New feature transforms** — the transforms module is extended and the new columns wired into
  the predictor lists: wire the existing-but-unused weight-change and distance-change
  calculations; add explicit field size / relative field size; an ordinal race-class encoding;
  age and race-relative age (reusing the existing race-context "Rel" machinery); draw features
  (draw percentile and relative draw) for flat races; race quality/eligibility one-hots
  (`Pattern`, `RatingBand`, `AgeBand`, `SexRestriction`); and surface-switch / code-switch flags.
  Features whose inputs are structurally sparse (draw on jumps, blank class) are added to the
  NaN-tolerant predictor list rather than the required list.
- **Second-tier builder extensions** — the horse-stats builder is extended (only if the first
  feature tier pays off) to emit `LastRaceHeadGear`, `LastRaceJockeyId`, and course/going/
  distance-conditioned prior-form aggregates, following the established leak-free as-of-date
  pattern; `Horse_Stats.csv` is regenerated.
- **Evaluation enrichment** — the evaluation script persists per-horse `WinProbability` for the
  field plus race-level context columns, and gains reporting for the coverage sweep, the
  ROI-vs-coverage frontier, and the early-vs-late stability split.
- **Diagnostic script** — a new analysis script (alongside the existing analysis scripts) joins
  the picks to the raw results for field/class context and reports per-segment win-rate and ROI,
  confidence-band performance, and calibration. Its outputs are the proposed hard-race rules
  (with out-of-sample effect) and the feature nominations.

**Schema and wiring changes**

- The evaluation results CSV changes from one-row-per-pick to carrying per-horse win-probability
  rows (or an added probability column) plus race-context columns.
- The prediction card column set (and the evaluation card extraction) gains the already-available
  card fields needed for the new features and rules: `CourseId`, `Class`, `StallNumber`, `Age`,
  `Pattern`, `RatingBand`, `AgeBand`, `SexRestriction`. No rating or odds columns are added.
- `run.ps1` wiring is unchanged: the abstain layer lives inside the active algorithm, so the
  production prediction step simply returns fewer races. No new CLI verb is introduced; the C#
  downloader is untouched.

## Testing Decisions

- A good test asserts external behaviour, not implementation detail: pure functions are exercised
  with small synthetic DataFrames, and algorithm behaviour is driven through `fit`/`predict` on
  fixtures. Prior art: the transforms, horse-stats, binary-win-classifier and evaluate test
  modules under `tests/`, which mirror the package layout.
- **Confidence gate (tested):** synthetic per-horse probabilities → correct keep/abstain for
  both metrics (top-pick probability and gap-to-second), threshold/coverage edge cases, and
  empty-race handling.
- **Hard-race rules (tested):** each individual rule and the combined gate, including
  structural-blank handling (e.g. a race with no class or no rating band).
- **New feature transforms (tested):** extend the transforms tests for the weight/distance-change
  wiring, ordinal race-class encoding (including the "Other"/blank bucket), draw features
  (including null on jumps), age and relative-age, the quality/eligibility one-hots (including
  the "None"/blank category), and the switch flags.
- **Not given dedicated tests** (verified via evaluation/run output instead, per agreement): the
  second-tier horse-stats builder extensions, the evaluation enrichment / CSV-schema change, and
  the diagnostic script. Pure helpers within these may still receive light tests opportunistically;
  where a conditioned-form aggregate is added, a leak-safety assertion (current race excluded)
  should mirror the existing proxy-TSR as-of-date tests.

## Out of Scope

- Value/overlay or any market-aware betting, and any odds-derived feature — odds are not
  available at prediction time.
- A standalone ensemble/stacking of the registered algorithms, and full probability
  recalibration as its own pillar (the confidence gate uses the raw probabilities as-is).
- Variable staking (e.g. Kelly); flat £1 stakes are retained for comparability.
- Multiple bets per race; the model still backs at most one horse per race.
- Re-tuning ProxyTSR hyperparameters (the tuned variant was already evaluated and trailed).
- Any change to the C# downloader, its parsers, or the set of CLI verbs.

## Further Notes

- The diagnostic is hypothesis-generation only. Discovered patterns (rules, thresholds, feature
  ideas) are then validated walk-forward; nothing observed on the full window is hard-coded from
  hindsight.
- The profitable-looking [5–8) decimal-odds band seen in the picks is a *diagnostic clue only*
  and must never become a betting rule — the price is unknown when the bet is placed.
- `FieldSize` as a raw count is constant within a race, so a "relative field size" feature must
  be normalised against a historical/card-derived baseline (e.g. the course/distance-typical
  field size), never a same-day cross-race or odds-based quantity.
- Field size has a minor train/serve definition skew (late non-runners between card download and
  the off); this is a data-completeness caveat, not leakage.
- Relevant memory: odds-unavailable-at-prediction-time, ratings-leakage, and the eval-pipeline
  design notes capture the constraints this PRD must respect.
