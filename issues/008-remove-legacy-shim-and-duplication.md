# 008 — Remove the `from_legacy` shim and the duplicated four-frame predict paths

**Type:** AFK
**Parent RFC:** `issues/001-unify-prediction-data-path-racedata.md`
**Status:** Proposed
**Blocked by:** `issues/007-migrate-harness-evaluate-predict.md`

RFC migration step 5 — final cleanup. Once every algorithm and the harness consume `RaceData`, delete the
transitional scaffolding and the now-dead duplicated code.

## What to build (delete)

- `RaceDataBuilder.from_legacy(...)` and the transitional four-frame adapter added in issue 003.
- Any remaining four-frame `predict(...)` / `predict_field(...)` signatures on `base.py` and subclasses.
- The duplicated pipeline bodies that are now unreachable (the old `_run_prediction` in
  `binary_win_classifier.py`, the old `predict` in `regressor.py`).
- `decompose_race_history` in `features/race_history.py` if it has no remaining callers (and `race_card`
  if likewise unused).

## Acceptance criteria

- [ ] No `from_legacy` references remain; the four-frame `(races, horse_stats, jockey_stats, trainer_stats)`
      signature is gone from the algorithm contract.
- [ ] `grep` confirms `decompose_race_history` has zero callers, or it is retained with a documented reason.
- [ ] The merge/encode/complete-race/rank pipeline exists in exactly one place (`RaceDataBuilder` + the base
      engine template).
- [ ] `python -m pytest tests/` green; `tests/features/test_race_history.py` updated/removed as appropriate.

## Tests

Remove tests that only exercised the deleted shim / four-frame signature; ensure no coverage of live behavior
is lost (the behavior now lives behind the engine-boundary and builder characterization tests).

## Notes

- Out of scope (separate RFC candidates, per 001): centralizing scattered hyperparameters, replacing the
  index-based `ACTIVE_ALGORITHM` registry, and collapsing the thin weighting/objective subclasses into
  composable strategy objects.
