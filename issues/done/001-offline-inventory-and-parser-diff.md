# 001 — Offline inventory, parser diff & method foundation

## Parent PRD

`issues/prd.md` — *Audit extra data available on Racing Post today's race cards (research-only)*

## What to build

The deterministic, offline foundation of `docs/racecard-extra-data-audit.md`. **No production
code changes** — this is research that reads existing fixtures and the existing parsers and
writes a markdown doc.

Concretely, against the 5 existing full-page card fixtures in
`RacePredictor.Core.Tests/RacingPost/Examples/` (Yarmouth flat-turf, Kempton AW/headgear,
Warwick hurdles, Gowran Park IRE/unrated, Happy Valley HK — all `_20260520`):

1. **Inventory** every `data-testid` value present in each card page.
2. **Diff** that inventory against the set the existing parsers consume —
   `RacePredictor.Core/RacingPost/RaceCardRunnerParser.cs` and
   `RacePredictor.Core/RacingPost/RaceCardParser.cs` — to yield an exhaustive list of
   **ignored** DOM hooks.
3. **Scan for non-`data-testid` content**: the `<sup>` badges on the jockey/trainer anchors
   that `RaceCardRunnerParser` notes but discards ("booking count, win-rate"), plus any
   free-text comment blocks (Spotlight / RP verdict / race comments) regardless of tagging.
4. **Lightweight backfill presence-check**: for each candidate field, check whether it also
   appears in the existing `results_*.html` fixtures (presence-check only — not a full
   result-parser audit), to seed the backfill-able flag.

This issue **starts** the deliverable doc with three sections fully populated, leaving the
per-candidate judgement and live-pull evidence to issues 002/003:

- **Method note** — the inventory-diff technique and the corpus listed (the 5 fixtures named,
  with their `_20260520` date; a placeholder for the two live pulls issue 002 adds).
- **Raw ignored-`data-testid` appendix** — the full set of card `data-testid`s NOT consumed by
  the parsers (PRD user story 12 / Testing-Decisions "reproducible inventory").
- **Draft candidate inventory** — one row per ignored signal with the columns derivable
  offline now: *field / DOM hook*, *backfill-able? (also on result fixtures)*, and a stub for
  the columns issues 002/003 fill (availability, coverage, leakage, type/difficulty, rationale,
  verdict). Must include the `<sup>` badges and the named soft set as rows even if their
  availability is still TBD.

## Acceptance criteria

- [x] `docs/racecard-extra-data-audit.md` exists with a **Method** section naming the 5 card
      fixtures (and their date) and the inventory-diff + non-`data-testid`-scan technique.
- [x] A **Raw ignored `data-testid` appendix** lists every card `data-testid` not consumed by
      `RaceCardRunnerParser`/`RaceCardParser`, derived from the named fixtures.
- [x] A **draft candidate inventory table** is present with one row per ignored signal,
      including explicit rows for the `<sup>` jockey/trainer badges and for each named soft
      field (hot-trainer/jockey form flags, Spotlight, RP verdict, breeding sire/dam, owner,
      headgear-change / wind-op flags, jockey allowance).
- [x] Each candidate row carries a **backfill-able?** value grounded in an actual presence (or
      absence) check against the `results_*.html` fixtures — no unsupported claims.
- [x] The doc compiles as valid markdown (tables render); no C# / Python source files are
      modified (confirm `git status` shows only `docs/` + `issues/` changes).

## Completion note (issue 001)

Delivered `docs/racecard-extra-data-audit.md` with the Method note, the raw ignored-`data-testid`
appendix (396 distinct → 19 consumed → 377 ignored, candidate-bearing subset listed; chrome
grouped), and the 19-row draft candidate inventory. Offline columns (field/source,
backfill-able?) are filled; availability/coverage carry `TBD-002`, leakage/type/rationale/verdict
carry `TBD-003`.

**Key finding for 002/003:** the card pages embed a `__NEXT_DATA__` JSON island whose per-runner
objects carry structured versions of nearly every soft field (`sireName`/`damName`, `ownerName`,
`horseHeadGearFirstTime`, `geldingFirstTime`, `windSurgery`, `weightAllowanceLbs`,
`jockeyFirstTime`, `trainerRtf`, `newTrainerRacesCount`, `countryOrigin`, `spotlight`, race-level
`verdict`). This likely collapses parse difficulty for most candidates from DOM/NLP to a JSON
read — but **002 must confirm `__NEXT_DATA__` is present in the public/logged-out DOM** (the
fixtures may have been captured under a particular session state). No dedicated "hot
trainer/jockey" flame flag exists; the in-form signals are `trainerRtf` + the trainer win-rate
`<sup>` badge + `newTrainerRacesCount` (noted in the doc for 003 to resolve).

Backfill grounded against `results_*.html`: result fixtures use legacy markup (no `__NEXT_DATA__`,
no `data-testid`); plain-text scan of `results_southwell_20260218_1655.html` → owner present
(backfill-able), breeding/verdict/wind-op absent (forward-only).

## Blocked by

None — can start immediately.

## User stories addressed

Reference by number from the parent PRD:

- User story 1 (partial — the candidate list exists; ranking/verdicts land in 003)
- User story 7 (backfill-able flag seeded from result fixtures)
- User story 10 (partial — the `<sup>` badges are captured as a row; verdict lands in 003)
- User story 12 (raw ignored-`data-testid` appendix)
- User story 13 (method documented + corpus listed)
- User story 14 (partial — backfill-able fields identified as input to the sibling item)
