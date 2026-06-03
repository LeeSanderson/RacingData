## Parent PRD

`issues/prd.md`

## What to build

A new analysis script under `race_analytics/scripts/` (alongside the existing analysis scripts)
that consumes the enriched eval results (joining the raw `Results_*.csv` where extra context is
needed) and characterises **when the model wins and loses**. It reports per-segment win-rate and
ROI, confidence-band performance, and a calibration view, and emits a ranked **candidate
hard-race-rule list** (each with its coverage cost and out-of-sample effect) plus a **feature
nomination list** tied to the weakest segments. This is the AFK build-and-run half of the
diagnostic; the human approval is the separate issue 003. See the PRD "Workstream 1 - Diagnostic".

## Acceptance criteria

- [ ] Running the script over the enriched results produces per-segment win-rate and ROI tables across at least: field size, class, race type, distance band, going, age band.
- [ ] It reports model performance by confidence band and a basic calibration view (predicted vs actual win rate).
- [ ] It outputs a ranked list of candidate hard-race rules, each annotated with its coverage cost and out-of-sample win-rate/ROI effect.
- [ ] It outputs a feature-nomination list pointing at the weakest segments.

## Blocked by

- Blocked by `issues/001-enriched-evaluation-output.md`

## User stories addressed

- User story 5
- User story 11
- User story 24
