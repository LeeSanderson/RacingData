# 006 — Migrate `GatedClassifier` to calibrate on the same `RaceData`

**Type:** AFK
**Parent RFC:** `issues/001-unify-prediction-data-path-racedata.md`
**Status:** Proposed
**Blocked by:** `issues/003-deepen-fieldpredictor-engine.md`, `issues/004-migrate-win-classifier-family.md`

RFC migration step 4. Remove the flat → decomposed → re-encode round trip in the gate's calibration,
which currently also re-derives `DaysRested` against `datetime.today()` instead of the fold date — a
latent calibration skew/leak.

## What to build

In `race_analytics/algorithms/gated_classifier.py`:

- `fit(data: RaceData)`: call `self._inner.fit(data)`, then calibrate the confidence gate directly from
  `self._inner.predict_field(data)` — the **same** `RaceData` the inner trained on. Delete the
  `decompose_race_history(race_history)` call (`gated_classifier.py:30`) and the four-frame re-encode.
- `predict_field(data)` / `predict_field_unfiltered(data)`: take `RaceData`; the rules gate reads
  `data` for race-level attributes. No re-merge/re-encode.

## Acceptance criteria

- [ ] `GatedClassifier.fit` no longer imports or calls `decompose_race_history`; calibration uses the same
      `RaceData` instance the inner was trained on.
- [ ] Calibration is computed against the fold date (`RaceData.as_of`), not wall-clock time — no
      `datetime.today()` anywhere in the gate path.
- [ ] On a fixed fixture, the calibrated threshold matches the previous (round-trip) implementation within
      tolerance.
- [ ] `tests/algorithms/test_gated_classifier.py` passes (migrated to the `RaceData` signature).
- [ ] `python -m pytest tests/` green.

## Tests

Extend `test_gated_classifier.py`: assert `decompose_race_history` is not called (e.g. patch/spy) and that
two `RaceData` with different `as_of` calibrate differently.

## Notes

- `ConfidenceGate` and `RaceRulesGate` are unchanged collaborators — only their inputs change from raw
  frames to `RaceData` / `RaceData.frame`.
