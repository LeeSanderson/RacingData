# 002 — `RaceData` value object + `RaceDataBuilder` + characterization test

**Type:** AFK
**Parent RFC:** `issues/001-unify-prediction-data-path-racedata.md`
**Status:** Done (2026-06-13) — `race_analytics/features/race_data.py` + `tests/features/test_race_data.py`
**Blocked by:** None — can start immediately

Foundation slice (RFC migration step 1). Purely additive — **no algorithm is modified**,
so it cannot change any prediction and the whole suite stays green.

## What to build

A new module `race_analytics/features/race_data.py`:

- `RaceData` — a frozen dataclass `(frame: pd.DataFrame, as_of: pd.Timestamp, max_horses: int = 10)` with:
  - `has_labels` (property) — True iff label columns (`Wins` / `Speed` / `FinishingPosition`) are present.
  - `feature_frame(feature_cols) -> pd.DataFrame` — the columns the estimator consumes.
  - `with_columns(**new_cols) -> RaceData` — copy + add columns (e.g. `LastProxyTSR`, `_w`).
  - `subset(mask) -> RaceData` — copy + row filter (e.g. an in-pipeline race gate).
- `RaceDataBuilder` — the single home of the merge + transform chain:
  - `from_legacy(races, horse_stats, jockey_stats, trainer_stats, as_of, max_horses=10) -> RaceData`
    — the migration shim. Reproduces **exactly** the merged/encoded intermediate that
    `BinaryWinClassifierAlgorithm._run_prediction` builds today (`binary_win_classifier.py:100-131`):
    horse_stats merge + `DaysRested`, jockey_stats merge + `DaysSinceJockeyLastRaced` (both clamped
    `>10 → 10`, `LastOff` dropped with `errors="ignore"`), optional trainer_stats, then the
    encode/calculate chain incl. `encode_headgear`, `_add_race_context`, `calculate_draw_features` last.
  - `build_training(raw, as_of, max_horses=10) -> RaceData` (with labels) and
    `build_serving(card, history, as_of, max_horses=10) -> RaceData` (without labels) — both run the
    **identical** chain in the **identical** canonical order, declared once as an inspectable ordered list.
- **Key fix:** `DaysRested` / `DaysSinceJockeyLastRaced` are computed against `as_of`, **not**
  `datetime.today()`. `from_legacy` accepts an explicit `as_of` so the characterization can pin values.

## Acceptance criteria

- [x] `race_analytics/features/race_data.py` exists with `RaceData` + `RaceDataBuilder` (incl. `from_legacy`).
- [x] **Characterization (must pass):** on a fixed fixture, `RaceDataBuilder.from_legacy(...).frame` equals
      the post-encode `merged` intermediate of today's `_run_prediction` — column-for-column (same columns,
      order, dtypes, values, including the `>10` clamp and `errors="ignore"` drops), with a frozen `as_of`.
- [x] `build_training` / `build_serving` produce the same feature columns in the same order for the same rows
      (train==serve parity).
- [x] `python -m pytest tests/` green (395 passed); **no existing test file modified**.

## Tests

New `tests/features/test_race_data.py`. Build a small reusable fixture (a handful of races, one row per
horse-in-race, a known winner per race) — later slices reuse it. A frozen `as_of` makes `DaysRested`
deterministic.

## Notes

- The canonical encode order = the **classifier** path (the active `GatedRecencyWeightedWinClassifier`
  family). The regressor's minor order differences are reconciled when it migrates (issue 005) under its
  own characterization — not here.
- The transform free functions in `features/transforms.py` are unchanged; the builder only orchestrates them.
