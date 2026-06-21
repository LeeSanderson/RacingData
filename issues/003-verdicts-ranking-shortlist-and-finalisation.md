# 003 — Verdicts, ranking, shortlist & doc finalisation

## Parent PRD

`issues/prd.md` — *Audit extra data available on Racing Post today's race cards (research-only)*

## What to build

The judgement layer that turns the populated inventory into a **decision-ready** document, and
finishes the deliverable. **No production code changes.**

For each candidate row already carrying *field / DOM hook*, *availability*, *coverage*, and
*backfill-able?* (from issues 001/002), add the remaining assessment columns:

1. **Leakage status** — genuine pre-race fact vs post-race / updated-later — assessed with the
   same discipline as the `Card*`-vs-inherited-ratings distinction in `docs/data-pitfalls.md`
   (the reference standard). Leakage-suspect candidates are **capped at no-go**.
2. **Type & parse difficulty** — structured int/enum vs free-text NLP, so the follow-on capture
   PRD can estimate effort.
3. **Predictive rationale** — a one-line hypothesis for why the signal might move
   win-probability (hypothesis only; no empirical evaluation here).
4. **Verdict** — `go` / `no-go` / `defer` with a one-line reason, for **every** candidate.

Then finalise the doc:

- **Rank** the candidates by the PRD's ranking key — predictive plausibility ×
  (availability × coverage), penalised by parse difficulty; leakage-suspect capped at no-go;
  **backfill-able fields jump the queue** (usable immediately vs forward-only starvation).
- Add a top **"Recommended to capture next" shortlist** a follow-on PRD can copy-paste.
- Ensure the `<sup>` jockey/trainer badges and the full soft set each have an **explicit
  verdict** (no candidate silently dropped). An honest "nothing here clears the bar — defer"
  is an acceptable outcome; do not over-sell.
- Cross-reference any newly-found backfill-able field to the sibling `todo.md` item
  *"Backfill form / days-since / prize money into historic Results"*.
- Update `issues/todo.md`: the *"Research extra data available on Racing Post today's race
  cards"* entry links `docs/racecard-extra-data-audit.md` (relative link resolves) and is
  marked **researched**.

## Acceptance criteria

- [ ] Every candidate row has all assessment columns filled: leakage status, type & parse
      difficulty, predictive rationale, and a `go`/`no-go`/`defer` **verdict** with a reason.
- [ ] Any leakage-suspect candidate is capped at **no-go** (no leakage-suspect field appears in
      the shortlist).
- [ ] The doc has a top **"Recommended to capture next" shortlist** (copy-paste ready), ordered
      per the ranking key, with backfill-able fields prioritised.
- [ ] The `<sup>` badges and every named soft field (hot-trainer/jockey flags, Spotlight, RP
      verdict, breeding, owner, headgear-change/wind-op, jockey allowance) each have an explicit
      verdict — verified by inspection.
- [ ] `issues/todo.md` links the findings doc (relative link resolves), marks the item
      researched, and cross-references newly-found backfill-able fields to the sibling backfill
      entry.
- [ ] No C# / Python source files are modified (`git status` shows only `docs/` + `issues/`).

## Blocked by

- Blocked by `issues/001-offline-inventory-and-parser-diff.md`
- Blocked by `issues/002-live-availability-and-coverage-pulls.md`

## User stories addressed

Reference by number from the parent PRD:

- User story 4 (leakage status assessed against the `Card*` standard)
- User story 5 (type & parse difficulty)
- User story 6 (predictive rationale)
- User story 8 (explicit go/no-go/defer verdict per candidate)
- User story 9 (recommended-to-capture-next shortlist)
- User story 11 (explicit verdicts on the soft set)
- User story 15 (`todo.md` links the doc and marks the item researched)
- Completes user stories 1, 10, and 14 (begun in 001)
