# 006 — Migrate `GatedClassifier` to calibrate on the same `RaceData`

**Type:** AFK
**Parent RFC:** `issues/001-unify-prediction-data-path-racedata.md`
**Status:** Done (2026-06-13)
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

- [x] `GatedClassifier.fit` no longer imports or calls `decompose_race_history`; calibration uses the same
      `RaceData` instance the inner was trained on.
- [x] Calibration is computed against the fold date (`RaceData.as_of`), not wall-clock time — no
      `datetime.today()` anywhere in the gate path.
- [x] On a fixed fixture, the calibrated threshold matches the previous (round-trip) implementation within
      tolerance (legacy pinned at 0.3333; migrated within 1e-2).
- [x] `tests/algorithms/test_gated_classifier.py` passes (extended; the four-frame harness shape is still
      accepted via the inherited legacy adapter until issue 007).
- [x] `python -m pytest tests/` green (415 passed).

## Completion notes (2026-06-13)

- `GatedClassifier.fit(data)` now: if `data` is not a `RaceData`, wraps the flat training frame via the
  inherited `_training_data_from_legacy` (clamp + `as_of` = fold date, no re-encode); then
  `self._inner.fit(data)` and `self._calibrate(self._inner.predict_field(data))` — the **same** RaceData. The
  `decompose_race_history` import and the four-frame re-encode are deleted.
- **Why this kills the `datetime.today()` skew:** the in-sample calibration field is now produced from the
  training RaceData's own (fold-date) features, so `predict_field` takes the RaceData branch and never hits
  `from_legacy(as_of=datetime.today())`. Proven by `test_calibration_is_independent_of_wall_clock` (mocking
  `base.datetime.today` to two far-apart dates yields an identical threshold).
- `predict_field` / `predict_field_unfiltered` accept either a `RaceData` (rules gate reads `data.frame`) or
  the legacy four frames (rules gate reads the raw `races` card). The harness keeps calling the four-frame
  shape until issue 007; the RaceData shape is exercised by the new tests.
- `ConfidenceGate` / `RaceRulesGate` unchanged — only their inputs moved from raw frames to `RaceData.frame`.
- Threshold parity: on the uniform fixture the legacy round-trip and the new path both calibrate to ~1/3,
  because the only feature the two paths differ on (DaysRested: today-relative vs fold-date) has no variance
  in training and so never enters the model. In a real window the leak-free per-row features will shift the
  threshold slightly — the intended, bounded fix.

## Tests

Extend `test_gated_classifier.py`: assert `decompose_race_history` is not called (e.g. patch/spy) and that
two `RaceData` with different `as_of` calibrate differently.

## Notes

- `ConfidenceGate` and `RaceRulesGate` are unchanged collaborators — only their inputs change from raw
  frames to `RaceData` / `RaceData.frame`.
