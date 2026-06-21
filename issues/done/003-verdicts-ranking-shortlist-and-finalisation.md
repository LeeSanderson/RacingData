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

- [x] Every candidate row has all assessment columns filled: leakage status, type & parse
      difficulty, predictive rationale, and a `go`/`no-go`/`defer` **verdict** with a reason.
- [x] Any leakage-suspect candidate is capped at **no-go** (no leakage-suspect field appears in
      the shortlist).
- [x] The doc has a top **"Recommended to capture next" shortlist** (copy-paste ready), ordered
      per the ranking key, with backfill-able fields prioritised.
- [x] The `<sup>` badges and every named soft field (hot-trainer/jockey flags, Spotlight, RP
      verdict, breeding, owner, headgear-change/wind-op, jockey allowance) each have an explicit
      verdict — verified by inspection.
- [x] `issues/todo.md` links the findings doc (relative link resolves), marks the item
      researched, and cross-references newly-found backfill-able fields to the sibling backfill
      entry.
- [x] No C# / Python source files are modified (`git status` shows only `docs/` + `issues/`).

## Completion note (issue 003)

Finalised `docs/racecard-extra-data-audit.md` into a decision-ready deliverable. Filled the four
judgement columns for all 18 in-scope rows (row 19 = live odds, out of scope) and added a ranked
**"Recommended to capture next"** shortlist at the top.

**Verdict tally (every in-scope candidate has an explicit verdict):** 6 `go`, 7 `defer`, 5 `no-go`.

- **Leakage — explicit finding:** assessed against the `Card*`-vs-inherited-ratings standard in
  `data-pitfalls.md`, **no candidate is leakage-suspect** — all 18 are morning-card facts knowable
  before the race, so none was capped at no-go on leakage grounds (the no-gos are signal/cost
  calls). The only nuances are *currency* not leakage: `trainerRtf` is a daily-recomputed rolling
  stat that must be frozen at capture, and weather is a capture-time snapshot.
- **Type & parse difficulty:** rows 1–14 are low-cost `__NEXT_DATA__` JSON reads (the 002 finding).
  The costly exceptions are the **Verdict** (DOM scrape + light NLP, patchy coverage — not a JSON
  read) and **Spotlight** (cheap to bank raw, but a feature needs NLP).
- **Shortlist (go), ranked per the PRD key:** (1) trainer current form `trainerRtf`; (2) first-time
  flags bundle `horseHeadGearFirstTime`+`geldingFirstTime`+`jockeyFirstTime`; (3) breeding `sireName`
  (+`damName` add-on); (4) wind-surgery `windSurgery` (jumps-weighted); (5) **owner id** — the only
  backfill-able field, so it jumps the queue on *immediacy* as a low-regret enabler. Honest framing
  kept throughout: the high-value structured signals were already captured, the residual is
  soft/lower-signal, and all but owner are forward-only.
- **Deferred-but-attractive:** RP Verdict's named selection (tipster pick) and Spotlight prose —
  both deferred pending an NLP/text pipeline, not rejected on merit.
- **`<sup>` badges + soft set all have explicit verdicts:** win-rate `<sup>` (row 9, go via the
  `trainerRtf` JSON, not the badge), booking-count `<sup>` (row 10, no-go), Spotlight (14, defer),
  Verdict (15, defer), breeding (2 go / 3 defer), owner (1 go-enabler), headgear-first-time (4 go),
  wind-op (6 go), jockey allowance (7 defer), hot-form (resolved to row 9 + row 11).

**`todo.md`:** the *"Research extra data…"* entry is marked ✅ RESEARCHED (2026-06-21) and links the
doc via a resolving `../docs/...` relative path; the sibling *"Backfill form / days-since / prize
money…"* entry gains an owner cross-reference (owner is the newly-found backfill-able field).

**Feedback loops:** none run — docs/research only, no C#/Python source surface (consistent with the
PRD and issues 001/002). Verified against the issue's acceptance criteria: every row has all four
judgement columns + a verdict; no leakage-suspect candidate exists (so none in the shortlist);
copy-paste shortlist present and ranked; `<sup>` badges + soft set each have an explicit verdict;
`todo.md` links the doc and cross-refs the backfill sibling; `git status` shows only `docs/` +
`issues/`.

**Notes for next iteration:** this was the **last open AFK issue** of the PRD. With 001–003 all in
`issues/done/`, the research PRD is complete and is a `clean-up-prd` candidate (`issues/prd.md` +
the three done issue files can be archived). The deliverable `docs/racecard-extra-data-audit.md`
and the `todo.md` updates are durable and survive that cleanup. The natural follow-on is a separate
**capture PRD** that takes the shortlist directly.

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
