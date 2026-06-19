## Parent PRD

`issues/prd.md` — "Adoption is gated on honest data, not this run" (Implementation
Decisions), plus "Further Notes" (known risks; read the accuracy jump correctly).

## What to build

Run the full A/B walk-forward comparison across **every registered algorithm** with
`MarketProb` now available, and record the results as a **diagnostic** — explicitly NOT a
promotion decision. Because forecast coverage in history is ~zero, this eval is measuring
the SP placeholder, not the forecast feature production will serve on.

- Re-run the walk-forward eval over all algorithms in `ALGORITHMS` (fold count is the
  implementer's call at run time — the PRD says "full walk-forward comparison" and the
  cost is ~6–8 min/fold × 16 algorithms; choose a depth that gives a clear per-algorithm
  read without committing to a fixed number here).
- Record the per-algorithm accuracy / ROI / coverage in `evaluations.md` under a clearly
  flagged **"SP-placeholder / diagnostic"** section, so nobody later mistakes these for
  decision-grade forecast results.
- Document the known eval/production divergence: the expected accuracy jump reflects the
  classifiers leaning on the (SP-defined) favourite — "following the favourite", not a
  genuine forecast-time edge.
- **Do not change `ACTIVE_ALGORITHM`.**

## Acceptance criteria

- [ ] The eval has been run across all registered algorithms with `MarketProb` available
      (per-fold results saved via `--save-results`).
- [ ] `evaluations.md` has a new, clearly-labelled SP-placeholder/diagnostic section with
      each algorithm's accuracy/ROI/coverage and the "following-the-favourite" caveat.
- [ ] `race_analytics/algorithms/__init__.py` `ACTIVE_ALGORITHM` is unchanged (verified by
      diff: no edit to the active-algorithm selection).

## Blocked by

- Blocked by `issues/004-expose-market-prob-optional-predictors.md`
- Blocked by `issues/005-measurement-through-resolver.md`
- Blocked by `issues/006-diagnostic-logging-eval-csv.md`

## User stories addressed

- User story 14 (full A/B re-run across every registered algorithm)
- User story 15 (results recorded under a flagged SP-placeholder/diagnostic section)
- User story 16 (production `ACTIVE_ALGORITHM` left untouched)
- User story 19 (known SP-vs-forecast divergence documented)

---

## Progress — PAUSED 2026-06-18 (resume instructions)

Depth chosen: **14 folds**, 7-month training window, all 16 registered algorithms.
Run command was:
`python -m race_analytics.scripts.evaluate --folds 14 --training-months 7 --save-results --results-file evaluation_results_20260618.csv`

The run was stopped early (laptop shutdown). Partial results are in
**`evaluation_results_20260618.csv`** (repo working tree, **untracked** — it survives a
shutdown; do NOT `git clean`). The CSV is the reliable record: it is flushed atomically
once per fold *after* all 16 algorithms run, so any fold present in it is complete.
(Run stdout is block-buffered and unreliable for the final fold.)

### Fold status (fold dates run newest-first from yesterday=2026-06-17)

| Fold date | Status |
|---|---|
| 2026-06-17 | **Skipped** — "No known races". No rerun needed; not a gap. |
| 2026-06-16 | ✅ Complete (16 algos). |
| 2026-06-15 | ✅ Complete (16 algos). |
| 2026-06-14 | ✅ Complete (16 algos; smaller race day → fewer rows). |
| 2026-06-13 → 2026-06-04 | ⏳ **Not run** (killed at the start of 06-13). 10 folds remain. |

Note: some completed folds show <16 *distinct* algorithms in the CSV — that is normal,
an abstain algorithm emitting 0 rows on a low-confidence day, not incompleteness.

### To resume

`evaluate.py` derives fold dates from *yesterday* at run time, so the resume flags
depend on the resume date. Target the remaining dates **2026-06-13 → 2026-06-04** and
**append** to the same CSV. Compute (whole days):

- `offset = (resume_date − 1 day) − 2026-06-13`
- `folds  = offset + 10`
- Run (omit `--algorithms` to run all 16):
  `python -m race_analytics.scripts.evaluate --folds <folds> --training-months 7 --save-results --results-file evaluation_results_20260618.csv --fold-offset <offset>`

Worked examples:
- Resume **2026-06-19** → `offset = 5`, `folds = 15` → `--folds 15 --fold-offset 5`.
- Resume **2026-06-18** (same day) → `offset = 4`, `folds = 14` → `--folds 14 --fold-offset 4`.

After the append, verify the CSV's `FoldDate` set is exactly 2026-06-16 → 2026-06-04 (13
usable folds; 06-17 has no races) with no duplicate (FoldDate, Algorithm, RaceId,
HorseId) rows. If the offset was off and 06-14 got re-run, dedupe keeping the last
occurrence before aggregating.

### Then (remaining 007 work)

1. Aggregate per-algorithm **accuracy / ROI / coverage** from the CSV (and the
   favourite baseline), e.g. via `race_analytics/utils/scoring.py`.
2. Record them in `evaluations.md` under a clearly-flagged **"SP-placeholder /
   diagnostic"** section with the **"following-the-favourite"** caveat (the accuracy
   jump reflects classifiers leaning on the SP-defined favourite, not a forecast-time
   edge). Reference the raw CSV `evaluation_results_20260618.csv`.
3. Verify `race_analytics/algorithms/__init__.py` `ACTIVE_ALGORITHM` is **unchanged**.
4. Commit the CSV + `evaluations.md`, then move this issue to `issues/done/`.

---

## Completed — 2026-06-19

Resumed on 2026-06-18 with `--folds 14 --fold-offset 4` (the plan's worked example for that
date); the run finished cleanly (exit 0), appending folds 2026-06-13 → 2026-06-04 to
`evaluation_results_20260618.csv`. Final CSV: **13 usable folds** (2026-06-16 → 2026-06-04;
06-17 had no races), 14,576 rows, all **16 algorithms**, **0 duplicate** (FoldDate,
Algorithm, RaceId, HorseId) rows.

Per-algorithm accuracy / ROI / coverage + the favourite baseline were aggregated from the
CSV (reusing `scoring.py` + `MarketFavouriteBaseline`), **validated to 0.000 against the
evaluator's own printed 10-fold Summary** before applying to all 13 folds. Results recorded
in `evaluations.md` under the flagged **"SP-placeholder / diagnostic"** section with the
**following-the-favourite** caveat.

`ACTIVE_ALGORITHM` (`GatedRecencyWeightedWinClassifier`, `ALGORITHMS[13]`) **unchanged**
(verified: no git diff on `race_analytics/algorithms/__init__.py`).

Acceptance criteria all met. Headline: gated classifiers ~0.39–0.41 accuracy vs favourite
0.325, but ROI is negative across all full-coverage algorithms (favourite −£31.89) — the
accuracy lift is favourite-tracking via the SP-defined `MarketProb`, not a forecast-time
edge.
