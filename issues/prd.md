# PRD: Algorithm hierarchy refactor + `Last3*` coverage fix

## Problem Statement

Two problems, structurally linked.

**Coverage problem.** The 180-fold leak-free re-evaluation lands only **415 races**
where the prior baseline run saw **2,475**. The cause is well-understood
(see `evaluations.md`): commit `1f8c709` added seven columns to `PREDICTORS`,
and every algorithm's `predict()` requires every horse in a race to have
every `PREDICTOR` non-null (the `OriginalCount == PredictableCount` filter).
Three of those columns — `Last3RaceAvgSpeed`, `Last3RaceSpeedTrend`,
`Last3AvgRelFinishingPosition` — are NaN for **43.1%** of horses (any horse
with fewer than 3 prior races), so the whole-race predictability filter
excludes most of the field. The result is that per-pick accuracy is computed
over a narrow 415-race slice rather than the ~1,650 races the XGBoost-family
algorithms could actually predict.

**Structural problem.** Today's `BaseAlgorithm` is doing double duty: it is
both the abstract polymorphic interface (used by the `for algo in
selected_algos` loops in `evaluate.py` and the `ACTIVE_ALGORITHM` switch in
`predict.py`) **and** a concrete Speed-target sklearn-style regressor
implementation. `RatingsXGBoostAlgorithm` and `ProxyTSRXGBoostAlgorithm`
inherit from it but override `fit` and `predict` completely, leaving the
inherited regressor logic dead. The two classifier algorithms then duplicate
~150 lines each of nearly-identical two-tier dropna / XGBClassifier setup /
merging / ranking logic. There is no clean place to opt one column into
NaN-tolerance for some algorithms but not others.

These problems are linked because the coverage fix needs the structural
fix: the two-tier dropna (some columns required, others NaN-tolerated) only
makes sense if the algorithm hierarchy can express "I want this feature but
I don't require it to be present".

## Solution

Restructure the algorithm hierarchy first (Phase A), then layer the
coverage fix on top (Phase B).

**Phase A — Hierarchy refactor (behaviour-preserving).** `BaseAlgorithm`
becomes a pure abstract ABC describing the polymorphic contract. Two
concrete sibling middle classes provide the shared implementations:
`RegressorAlgorithm` (Speed-target sklearn pipeline + two-tier dropna)
and `BinaryWinClassifierAlgorithm` (Wins-target XGBClassifier + standard
merging + ranking + hook points). Concrete algorithms migrate to inherit
from whichever middle class fits. The 180-fold numbers should reproduce
exactly — same 415 races, same per-algorithm accuracy.

**Phase B — `Last3*` coverage fix.** Split `PREDICTORS` into
`REQUIRED_PREDICTORS` and `OPTIONAL_PREDICTORS`. Move the three `Last3*`
columns into `OPTIONAL_PREDICTORS`. Wire XGBoost-family algorithms to
opt into NaN-tolerance for those columns via the new
`nan_tolerant_predictors` class attribute. Ridge stays NaN-intolerant by
construction (sklearn pipeline can't handle NaN). Re-run the 180-fold;
expect XGBoost-family coverage to jump from 415 to ~1,650 races, Ridge
unchanged.

## User Stories

1. As a researcher running the 180-fold evaluation, I want race coverage
   for XGBoost-family algorithms to reflect what those algorithms can
   actually predict, so that per-pick accuracy is estimated over the full
   ~1,650-race sample rather than the 415-race subset.
2. As a developer adding a new algorithm, I want a clear abstract base
   class that declares `fit` and `predict` as the polymorphic contract,
   so that I know exactly what my subclass must implement.
3. As a developer reading `evaluate.py`'s `for algo in selected_algos`
   loop, I want every registered algorithm to honour the same interface
   via a shared base class, so that the polymorphic loop has a documented
   contract rather than relying on duck typing.
4. As a developer reading `predict.py`, I want `ACTIVE_ALGORITHM` to be
   any registered algorithm of the same shape, so that switching the
   live model is a one-line change.
5. As a developer adding a new Wins-target classifier, I want a
   `BinaryWinClassifierAlgorithm` base class that handles dropna /
   feature construction / merging / ranking, so that my algorithm shrinks
   to a few class attributes and one or two hook overrides.
6. As a developer adding a new Speed-target regressor, I want a
   `RegressorAlgorithm` base class that handles the standard sklearn
   pipeline plus two-tier dropna, so that my algorithm shrinks to
   defining `_create_model`.
7. As a developer adding a feature that's available for some horses but
   not all (e.g. `Last3*`, `LastProxyTSR`), I want to opt into
   NaN-tolerant handling via a class attribute, so that NaN-tolerant
   algorithms see the column where present without filtering out races
   where it's missing.
8. As a developer adding a per-algorithm predictability gate (e.g. the
   TSR-availability gate), I want a hook on the classifier base that
   slots into the standard prediction flow, so that the gate doesn't
   require re-implementing the whole pipeline.
9. As a developer adding a per-algorithm pre-processing step (e.g.
   ProxyTSR's proxy-model fit and as-of-date proxy attachment), I want
   `_prepare_training_df` and `_prepare_prediction_df` hooks on the
   classifier base, so that algorithm-specific feature derivation slots
   in cleanly.
10. As a developer reading the codebase, I want the duplicated ~150-line
    `fit`/`predict` blocks in `ratings_xgboost.py` and
    `proxy_tsr_xgboost.py` to be deduplicated onto the shared classifier
    base, so that changes to the shared behaviour touch one file.
11. As a developer maintaining the Ridge regression algorithm, I want
    `Last3*` to be excluded from Ridge's feature list (rather than
    silently breaking its NaN-intolerant pipeline), so that Ridge keeps
    fitting on the columns it can actually use.
12. As a researcher reading `evaluations.md`, I want the headline
    coverage and accuracy numbers to reflect the new fuller race sample,
    so that the comparison against the production anchor remains honest.
13. As a researcher choosing `ACTIVE_ALGORITHM`, I want the per-algorithm
    comparison to be computed over the broader race set, so that the
    choice generalises beyond the narrow 415-race slice.
14. As a developer landing Phase A, I want every existing unit test to
    keep passing without modification, so that I have strong evidence
    the refactor is behaviour-preserving.
15. As a developer landing Phase A, I want a small-fold smoke evaluation
    at the end of the phase to confirm the 415-race numbers reproduce
    within rounding, so that any regression the unit tests missed is
    caught before Phase B starts.
16. As a developer landing Phase B, I want a unit test asserting that
    XGBoost-family algorithms fit and predict successfully on race data
    where some horses have NaN `Last3*` columns, so that the coverage
    fix is locked into the test suite.
17. As a developer landing the PRD, I want a single full 180-fold
    re-evaluation at the end (rather than one per phase), so that the
    ~5h wall-time cost is paid once.

## Implementation Decisions

**Module-level constants (`algorithms/base.py`):**

- Split `PREDICTORS` into two lists:
  - `REQUIRED_PREDICTORS` — every existing predictor except the three
    `Last3*` columns. Includes the four `Trainer*` columns (their 0.1%
    NaN rate is low enough that keeping them required loses essentially
    nothing; moving them is out of scope).
  - `OPTIONAL_PREDICTORS` — `Last3RaceAvgSpeed`, `Last3RaceSpeedTrend`,
    `Last3AvgRelFinishingPosition`.
- Keep `PREDICTORS = REQUIRED_PREDICTORS + OPTIONAL_PREDICTORS` as a
  backward-compatibility alias. Retire only in a future PRD.

**Hierarchy shape:**

- `BaseAlgorithm` becomes an `abc.ABC` declaring `fit(train_df)` and
  `predict(races, horse_stats, jockey_stats, trainer_stats=None)` as
  abstract methods. Carries the shared `__init__` / `max_horses` and any
  helpers that genuinely deduplicate (e.g. the `OriginalCount ==
  PredictableCount` filter, the `max_horses` cap, the standard race-card
  merging utilities).
- `BaseAlgorithm.nan_tolerant_predictors: ClassVar[list[str]] = []` —
  the opt-in mechanism. Subclasses override.
- New `RegressorAlgorithm(BaseAlgorithm)` — encodes the current
  Speed-target sklearn-style regressor logic. Subclasses provide
  `_create_model()` returning a sklearn estimator/pipeline. Two-tier
  dropna uses `REQUIRED_PREDICTORS` as the required subset and
  `nan_tolerant_predictors` as the tolerated extras.
- New `BinaryWinClassifierAlgorithm(BaseAlgorithm)` — encodes the
  Wins-target XGBClassifier pattern currently duplicated across
  `ratings_xgboost.py` and `proxy_tsr_xgboost.py`. Exposes:
  - `extra_nan_tolerant_features: ClassVar[list[str]] = []` — feature
    columns added to the model beyond `REQUIRED_PREDICTORS +
    OPTIONAL_PREDICTORS` (e.g. `RATING_COLS`, `LastProxyTSR`). Treated
    as NaN-tolerant alongside `OPTIONAL_PREDICTORS`.
  - `_prepare_training_df(self, train_df) -> pd.DataFrame` — default
    identity; ProxyTSR overrides to fit the proxy model and attach the
    per-row as-of proxy.
  - `_prepare_prediction_df(self, merged) -> pd.DataFrame` — default
    identity; ProxyTSR overrides to merge the per-horse proxy.
  - `_apply_gate(self, predictable) -> pd.DataFrame` — default identity;
    `RatingsXGBoostAlgorithm` overrides to require non-null
    `LastRaceTopSpeedRating` for every horse.
- `MarketFavouriteBaseline` stays outside the hierarchy. It has a
  different `predict` signature (takes `RaceIds + results`) and is
  computed alongside the ML algorithms as a non-ML baseline, not as a
  polymorphic peer.

**Concrete algorithm migrations:**

- `RidgeRegressionAlgorithm` → `RegressorAlgorithm`. Empty
  `nan_tolerant_predictors`. `Last3*` are dropped from Ridge's effective
  feature list (sklearn's `Ridge` cannot tolerate NaN structurally).
- `XGBoostAlgorithm` → `RegressorAlgorithm`. Phase B sets
  `nan_tolerant_predictors = OPTIONAL_PREDICTORS`.
- `RatingsXGBoostAlgorithm` → `BinaryWinClassifierAlgorithm`.
  `extra_nan_tolerant_features = RATING_COLS`. `_apply_gate` enforces
  the TSR-availability gate.
- `RatingsXGBoostUngatedAlgorithm` → subclass of
  `RatingsXGBoostAlgorithm`. Overrides `_apply_gate` to identity.
- `ProxyTSRXGBoostAlgorithm` → `BinaryWinClassifierAlgorithm`.
  `extra_nan_tolerant_features = RATING_COLS + ["LastProxyTSR"]`.
  `_prepare_training_df` fits the inner `ProxyTSRModel` on the
  fold-train slice and attaches the per-row as-of proxy.
  `_prepare_prediction_df` merges the per-horse
  `compute_horse_proxy_tsr`. No gate override.
- `TunedProxyTSRXGBoostAlgorithm` → subclass of
  `ProxyTSRXGBoostAlgorithm` with tuned XGBClassifier hyperparameters.

**Phase split:**

- Phase A (issues 001–005) is strictly behaviour-preserving. The 180-fold
  numbers should reproduce: 415 races, same per-algorithm accuracy
  within rounding. Validated by existing unit tests + a small-fold
  smoke eval at the end of Phase A.
- Phase B (issues 006–008) is the behaviour-changing layer. Issue 006
  flips `Last3*` into the NaN-tolerant tier. Issue 007 runs the full
  180-fold (HITL). Issue 008 updates `evaluations.md` and reviews
  `ACTIVE_ALGORITHM` on the new sample (HITL).

**Polymorphic contract preserved:**

- `evaluate.py`'s `for algo in selected_algos: algo.fit(train_df);
  algo.predict(card, horse_stats, jockey_stats, trainer_stats)` works
  unchanged.
- `predict.py`'s `algorithm.fit(race_features); algorithm.predict(card,
  horse_stats, jockey_stats, trainer_stats)` works unchanged.
- `ALGORITHMS` and `ACTIVE_ALGORITHM` in `algorithms/__init__.py` keep
  their current shape; only the inheritance hierarchy of the listed
  classes changes.

## Testing Decisions

**Phase A:**

- Every existing unit test under `tests/race_analytics/algorithms/` must
  pass unchanged through Phase A. This is the primary behaviour-preservation
  guarantee.
- Issue 002 adds a focused test that `RegressorAlgorithm.fit` correctly
  applies two-tier dropna: rows with NaN in any `REQUIRED_PREDICTORS`
  column are dropped; rows with NaN in a `nan_tolerant_predictors`
  column are kept (sklearn pipeline permitting).
- Issue 003 adds focused tests that `BinaryWinClassifierAlgorithm`
  invokes the four hooks (`_prepare_training_df`,
  `_prepare_prediction_df`, `_apply_gate`, and the
  `extra_nan_tolerant_features` opt-in) at the documented points in
  `fit` and `predict`.
- End of issue 005: small-fold smoke eval (e.g. 14-fold) confirming
  per-algorithm accuracy and race counts reproduce the existing 415-race
  numbers within rounding. Caught any regression the unit tests missed.

**Phase B:**

- Issue 006 adds a unit test asserting XGBoost-family algorithms fit and
  predict successfully on training data where some horses have NaN
  `Last3*` columns, with assertions on the kept-row count to lock in
  the tolerance.
- Issue 007 runs the full 180-fold re-evaluation (HITL — ~5h wall time).
  Expectation: XGBoost-family race coverage jumps from 415 to ~1,650;
  Ridge coverage roughly unchanged. Per-algorithm accuracy is compared
  against the Phase A baseline to check the broader sample doesn't
  materially degrade per-pick quality.

**Test style:** consistent with the existing `tests/race_analytics/`
convention — tests live in `tests/race_analytics/algorithms/` mirroring
the package structure, drive algorithms via their public `fit`/`predict`
interface, and assert on the resulting `DataFrame` rather than internal
collaborators. No new fixtures required beyond what existing tests
provide; small synthetic frames suffice.

## Out of Scope

- **Moving `Trainer*` columns into the NaN-tolerant tier.** Their NaN
  rate is 0.1% (essentially universal coverage); moving them buys
  nothing measurable and would change behaviour without a clear benefit.
  Stays in `REQUIRED_PREDICTORS`.
- **Changing the `MarketFavouriteBaseline` interface.** Its different
  signature is intentional — it's a non-ML baseline, not a polymorphic
  algorithm.
- **Adding a third algorithm family.** The new hierarchy supports
  extension (e.g. a Bayesian ranker, an ensemble), but no such
  algorithm is in scope.
- **Re-tuning XGBoost hyperparameters on the broader race sample.** The
  refactor is structural, not a hyperparameter search.
- **Re-anchoring against new production logs.** The production anchor
  (0.265 accuracy over 514 bets from 2026) is what we have; recomputing
  is a separate concern.
- **Retiring the `PREDICTORS` alias.** Kept for backward compatibility
  with any scripts that reference it directly. Can be removed in a
  future PRD once usage is audited.
- **Re-evaluating `ACTIVE_ALGORITHM` mid-PRD.** The choice stays as
  `ProxyTSRXGBoostAlgorithm` through Phases A and B; issue 008
  re-examines it on the new sample at the end.

## Further Notes

- **Why one PRD, not two:** the refactor is motivated by the coverage
  fix; splitting them artificially separates "why we're doing this"
  from "what we're doing". One PRD keeps the narrative coherent.
- **Why Phase A first:** the refactor lands as pure restructure with
  no behaviour change. This lets us answer "did anything break?" before
  layering on "did the coverage change degrade accuracy?". Without the
  phase split, a regression in Phase B would have two suspects.
- **Why `nan_tolerant_predictors` as a class attribute:** it expresses
  the algorithm's intent declaratively. Compare to passing it through
  `fit`'s arguments, which would couple every caller to the column
  split. The class-attribute form also makes Ridge's structural
  NaN-intolerance obvious at the class level.
- **Hook set deliberately small.** Three hooks plus a class attribute
  on `BinaryWinClassifierAlgorithm` covers every variation present in
  today's two classifier algorithms (TSR gate, proxy fit/merge,
  RATING_COLS, LastProxyTSR). More elaborate extension points can be
  added later if a new algorithm needs them.
- **`ProxyTSRModel`'s leak-free `compute_as_of_proxy` and
  `compute_horse_proxy_tsr`** stay unchanged — they're already correct
  from the previous PRD. This PRD only restructures how they plug into
  the classifier base.
- **Validation discipline.** The Phase A smoke eval is the cheap signal;
  the Phase B full 180-fold is the expensive one. Paying the latter
  once at the end of the PRD is the right cost trade-off.
