## Type

HITL — requires human design review before implementation.

## Parent PRD

`issues/prd.md`

## What to consider

The algorithm hierarchy has grown organically across issues 013–016 into a mix of inheritance chains and multiple-inheritance combos (e.g. `AbstainWrapperSplitAlgorithm(AbstainWrapperAlgorithm, SplitRaceTypeAlgorithm)`). Before adding further variants, consider whether the codebase would benefit from a more composable design.

## Questions to resolve

- **Mixins vs composition:** The current pattern uses multiple inheritance (MRO-dependent). Would explicit composition (wrapping an inner algorithm) be clearer and easier to test in isolation?
- **What are the stable axes of variation?** Currently: abstain gating, recency weighting, race-type splitting, position weighting, LTR scoring. Are these truly orthogonal, or do some conflict when combined?
- **Can wrapping be made generic?** `AbstainWrapperAlgorithm` hard-codes its inner model. A generic `AbstainWrapper(inner_algo)` factory would allow any base algorithm to be wrapped without a new class per combination.
- **Test surface:** Each new combination class currently needs its own test file. Composable building blocks would let tests cover the primitives and trust composition.

## Suggested starting point

Review `race_analytics/algorithms/abstain_wrapper.py`, `split_race_type.py`, and `proxy_tsr_xgboost.py` side-by-side. Sketch the dependency graph of what each class overrides, then decide if a decorator/wrapper pattern or protocol-based composition would flatten the hierarchy without breaking the eval pipeline.

## Acceptance criteria

- [x] Human has reviewed the current algorithm hierarchy and decided on a refactor strategy (or explicitly decided to leave it as-is).
- [x] If proceeding: a follow-up AFK issue is written with a concrete plan before any code changes.

## Outcome

Decided to proceed with a full composability refactor. See `issues/020-algorithm-composability-implementation.md` for the concrete implementation plan. Key decisions:

- Replace MRO-based composition with a true `GatedClassifier(inner)` decorator.
- Change `fit()` to receive `race_history` (enriched DataFrame); wrapper decomposes it via `decompose_race_history()` to call `predict_field()` for calibration — no shared private state.
- Rename all algorithms to descriptive-intent names (`WinClassifier`, `RecencyWeightedWinClassifier`, `GatedRecencyWeightedWinClassifier`, etc.).
- One substantive file per algorithm; thin registry subclasses in `__init__.py`.
- `SplitDisciplineWinClassifier` accepts `inner_class` parameter for cross-axis composition.
- Eval CSVs and `evaluations.md` to be updated with new names.

## Blocked by

- `issues/017-evaluation-run.md` — refactoring scope should be informed by which algorithms survive the full eval.
- `issues/018-adopt-algorithm-from-eval.md` — no point composing variants of a discarded algorithm.
