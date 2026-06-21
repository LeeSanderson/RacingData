# PRD: Audit extra data available on Racing Post today's race cards (research-only)

> **Type:** research / audit. **No production code changes.** The single deliverable is a
> decision-ready findings document. Implementation of any chosen field is deferred to a
> separate follow-on capture PRD.

## Problem Statement

The `todaysracecards` scraper captures a fixed set of pre-race columns into the race-card
data (form figures, draw/stall, weight, age, headgear, days-since-last-run, race class,
distance, prize money, and the three pre-race `Card*` ratings). The most recent pre-race
racecard-data PRD harvested the obvious structured signals, but the Racing Post card page
almost certainly exposes *more* — and we don't have a systematic, evidence-based account of
what we're leaving on the table.

Two specific gaps are already visible from the code itself: `RaceCardRunnerParser` notes but
**discards** `<sup>` badges on the jockey/trainer anchors ("booking count, win-rate"), and a
range of "soft" signals (RP Spotlight/verdict commentary, hot-trainer/jockey form flags,
breeding, owner, headgear-change/wind-op flags, jockey allowance) are unaccounted for. Before
spending scraper effort on any of these, we need to know: **which exist in the public DOM,
how well-covered they are, whether they are pre-race-safe (no leakage), how hard they are to
parse, and — critically — whether they could be backfilled across history** rather than
starving forward-only.

Without that audit, any decision to capture new card fields is made blind, and card capture
is forward-only with no archive — so a wrong pick costs months of empty training rows before
we even learn it was low-value.

## Solution

A single focused research session that audits the race-card DOM against what the scraper
already consumes, and produces **`docs/racecard-extra-data-audit.md`**: a durable findings
document with a ranked, decision-ready candidate list. A follow-on capture PRD can later pick
fields straight off the top of that list without re-doing the analysis. The `todo.md` backlog
entry is updated to link the doc and mark the item researched.

The audit is deliberately **research-only** — no parser/scraper/model code is touched. It
mirrors how `docs/odds-capture.md` underpinned the MarketProb work: durable reference that
survives the eventual `clean-up-prd` archival of this PRD.

## User Stories

1. As a modeller choosing what to capture next, I want a ranked list of card signals the
   scraper currently ignores, so that I can pick high-value features without re-auditing the
   page myself.
2. As a modeller, I want each candidate's **public-DOM availability** recorded, so that I
   don't scope capture work for a field that turns out to be members-only or absent.
3. As a modeller, I want each candidate's **coverage across race types** (flat vs jumps, GB
   vs IRE vs HK), so that I know whether a signal is universal or only present on, say, jumps
   cards.
4. As a modeller wary of leakage, I want each candidate's **leakage status** assessed with the
   same discipline as `Card*` vs inherited ratings, so that a post-race-or-later field never
   gets promoted as a pre-race feature.
5. As an engineer scoping the follow-on capture work, I want each candidate's **type and parse
   difficulty** noted, so that I can estimate effort (structured int/enum vs free-text NLP).
6. As a modeller, I want a **predictive rationale** per candidate, so that I understand why a
   signal might move win-probability before investing in capturing it.
7. As a modeller fighting forward-only data starvation, I want each candidate flagged as
   **backfill-able** (also present on daily result pages), so that I can prioritise fields
   usable immediately over fields that stay empty for months.
8. As a developer, I want an explicit **verdict (go/no-go/defer)** per candidate with a
   one-line reason, so that the list is decision-ready rather than just descriptive.
9. As a developer, I want a **"recommended to capture next" shortlist** at the top of the doc,
   so that a follow-on PRD can copy-paste it directly.
10. As a developer reviewing the audit, I want the concrete `<sup>` jockey/trainer badges
    ("booking count, win-rate") that the parser already discards to get an **explicit verdict**,
    so that this already-spotted, structured, classic predictor isn't lost.
11. As a developer, I want explicit verdicts on the soft set (hot-trainer/jockey form flags,
    Spotlight/RP-verdict commentary, breeding, owner, headgear-change/wind-op flags, jockey
    allowance), so that none of the named candidates is silently dropped.
12. As a reviewer, I want a **raw inventory of ignored `data-testid` values** as an appendix,
    so that I can verify the audit was exhaustive and not cherry-picked.
13. As a developer, I want the **method documented** (inventory-diff approach + corpus listed
    with dates), so that the audit is reproducible as the page markup evolves.
14. As a maintainer of the backlog, I want any newly-found backfill-able fields noted as input
    to the sibling "Backfill form / days-since / prize money into historic Results" item, so
    that the two research threads stay connected.
15. As a future reader, I want `todo.md` to link the findings doc and mark the item researched,
    so that the backlog reflects the current state.

## Implementation Decisions

This is a research deliverable; "implementation" means producing the document, not changing
the pipeline.

- **Deliverable:** a new durable doc `docs/racecard-extra-data-audit.md`. Chosen over a
  `todo.md` expansion (would bloat a lightweight backlog) and over a direct capture PRD (jumps
  the decision gate). Lives in `docs/` alongside `odds-capture.md` / `data-pitfalls.md` so it
  survives this PRD's eventual archival.
- **Audit technique:** enumerate the full set of `data-testid` values present in a card page
  and diff against the set the existing parsers consume (`RaceCardRunnerParser`,
  `RaceCardParser`), yielding an exhaustive list of ignored DOM hooks. Supplement with a scan
  for **non-`data-testid`** content — the `<sup>` badges on jockey/trainer anchors and any
  free-text comment blocks — since not everything is tagged.
- **Corpus (hybrid):**
  - *Primary* — the 5 existing full-page fixtures in
    `RacePredictor.Core.Tests/RacingPost/Examples/` (Yarmouth flat-turf, Kempton AW/headgear,
    Warwick hurdles, Gowran Park IRE/unrated, Happy Valley HK), all dated 2026-05-20.
  - *Supplement* — 2 fresh live GB pulls (one flat handicap, one jumps) loaded via
    `PuppeteerHtmlLoader` (plain HTTP is 429-blocked per `AGENTS.md`). These matter because
    the soft fields (Spotlight, RP verdict, hot-trainer/jockey badges) may be members-only or
    absent from the public DOM — establishing that is itself a key finding, and thin midweek
    fixtures could yield a false "not available".
- **Per-candidate assessment columns:** field / DOM hook · public-DOM availability · coverage
  across corpus (flagging flat-vs-jumps and GB-vs-intl gaps) · leakage status (genuine
  pre-race fact vs post-race/updated-later) · type & parse difficulty · predictive rationale
  (hypothesis) · backfill-able? (also on daily result pages) · verdict (go/no-go/defer +
  one-line reason).
- **Backfill-able flag:** determined by a **lightweight presence-check** against the existing
  `results_*.html` fixtures only — not a full result-parser audit. Any new backfill-able field
  is recorded as *input to* the sibling backfill backlog item, not scoped here.
- **Ranking key:** predictive plausibility × (availability × coverage), penalised by parse
  difficulty. Leakage-suspect candidates are **capped at no-go** regardless of appeal.
  Backfill-able fields jump the queue (usable immediately vs forward-only starvation).
- **`<sup>` badges stay inside the research boundary:** they are expected to rank highly
  (structured, already in the DOM, classic predictor) but implementation still routes through
  the follow-on capture PRD — no fast-track exception.
- **No production code changes.** No parser, command-handler, CSV-schema, `run.ps1`, or Python
  changes are made by this PRD.

## Testing Decisions

There is no production code to test — this PRD touches no C# or Python (consistent with the
prior documentation-only issue, which ran no `dotnet`/`pytest` gates because there was no
applicable surface). Verification is against the document's definition of done rather than an
automated suite:

- The findings doc contains all required sections: method note, ranked candidate table (all
  columns above), top "recommended to capture next" shortlist, explicit verdicts on every
  must-include candidate, and the raw ignored-`data-testid` appendix.
- Every must-include candidate (the `<sup>` badges + the soft set) has an explicit verdict —
  checked by inspection.
- The backfill-able presence-checks are grounded in the actual `results_*.html` fixtures (no
  unsupported claims).
- The `data-testid` inventory is reproducible: the diff is derived from the named fixtures and
  the two live pulls, with the live-pull dates recorded.
- `todo.md` links the doc and the relative link resolves; the backlog item is marked
  researched; newly-found backfill-able fields are cross-referenced to the sibling item.

If the audit incidentally surfaces a markup discrepancy that would affect an existing parser,
it is **recorded as a finding** in the doc — not fixed here.

## Out of Scope

- **No parser/scraper code changes** — audit only.
- **No implementing backfill** — backfill-able fields are flagged as input to the sibling
  "Backfill form / days-since / prize money into historic Results" `todo.md` item.
- **No deep result-page audit** — only lightweight presence-checks against existing
  `results_*.html` fixtures.
- **No re-assessing already-captured fields** — `FormFigures`, `StallNumber`, `Weight`, `Age`,
  `HeadGear`, `DaysSinceLastRun`, race `Classification`/class, `Distance`,
  `PrizeMoney`/`PrizeMoneyValue`, and the three `Card*` pre-race ratings are settled and not
  revisited.
- **No model/feature-engineering work** — predictive rationale is a hypothesis recorded in the
  doc, not an empirical evaluation.
- **No follow-on capture PRD** — that is a separate piece of work the shortlist feeds.

## Further Notes

- Size: a single focused research session. The corpus is mostly already on disk; the live
  pulls and the inventory-diff are quick; the bulk of the effort is judgement per candidate.
  This is intentionally lighter than a multi-issue PRD.
- Forward-only context: card capture has no archive, so a card-sourced field yields zero
  training rows until forward data accrues — which is exactly why the backfill-able flag is a
  primary ranking lever, and why getting the *shortlist* right matters more than breadth.
- Honest framing carried over from the trimmed `todo.md` entry: the high-value structured
  pre-race signals were already captured by the previous PRD, so the residual surface is
  largely soft/textual or lower-signal. The audit should not over-sell its findings; a
  legitimate outcome is "nothing here clears the bar — defer."
- Leakage discipline: the `Card*`-vs-inherited-ratings distinction in `docs/data-pitfalls.md`
  is the reference standard for the leakage-status column.
