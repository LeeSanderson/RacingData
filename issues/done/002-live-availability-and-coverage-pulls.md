# 002 — Live availability & coverage pulls

## Parent PRD

`issues/prd.md` — *Audit extra data available on Racing Post today's race cards (research-only)*

## What to build

The live-DOM evidence layer of `docs/racecard-extra-data-audit.md`. **No production code
changes** — this uses the existing `RacePredictor.Core/RacingPost/PuppeteerHtmlLoader.cs`
(plain HTTP is 429-blocked per `AGENTS.md` / memory) to pull fresh pages and records what it
finds back into the doc started by issue 001.

1. **Two fresh live GB pulls** via `PuppeteerHtmlLoader`: one **flat handicap** card and one
   **jumps** card. Save the pulled HTML alongside the analysis (or under the scratchpad) and
   **record the pull dates** in the doc's Method section (replacing issue 001's placeholder).
   These matter because the soft fields (Spotlight, RP verdict, hot-trainer/jockey badges) may
   be **members-only or absent** from the public DOM — establishing that is itself a key
   finding, and thin midweek fixtures could otherwise yield a false "not available".
2. For each candidate row in issue 001's inventory, fill the **public-DOM availability** column
   (present in public DOM / members-only / absent) using the live pulls plus the 5 fixtures.
3. Fill the **coverage across corpus** column, explicitly flagging flat-vs-jumps and
   GB-vs-IRE-vs-HK gaps (e.g. a signal present only on jumps cards, or absent from the HK card).

**AFK-with-fallback:** if the environment cannot reach racingpost.com headless, degrade to the
5 existing fixtures only and **record that explicitly** as a method caveat + a finding (the
availability column then reflects fixture-only evidence). Do not block the doc on the live pull.

## Acceptance criteria

- [x] The doc's **Method** section records the two live-pull dates and the two meeting/race
      types (flat handicap + jumps), OR an explicit caveat that live pulls were unavailable and
      the audit fell back to the 5 fixtures.
- [x] Every candidate row from issue 001 has a **public-DOM availability** value
      (present / members-only / absent), justified by the live pulls and/or fixtures.
- [x] Every candidate row has a **coverage across corpus** value that calls out flat-vs-jumps
      and GB-vs-international gaps where they exist.
- [x] The soft set specifically (Spotlight, RP verdict, hot-trainer/jockey badges) has its
      public-vs-members-only status resolved (or marked "unable to determine" with reason).
- [x] No C# / Python source files are modified (`git status` shows only `docs/`, `issues/`, and
      any saved-HTML/scratch artefacts).

## Completion note (issue 002)

**Live pulls succeeded — no AFK fallback needed.** Network was reachable and headless Puppeteer
worked, so two fresh **logged-out** GB cards were pulled **2026-06-21** via `PuppeteerHtmlLoader`
(through a throwaway harness in the session scratchpad that reuses the loader):

- **Flat handicap** — Brighton race `921242`, *"Flat Turf, Handicap, Class 5"*.
- **Jumps** — Hexham race `921033`, *"Chase Turf, Handicap, Class 4"* (summer NH).
- (supplementary) Brighton race `921240`, *"Flat Turf, Maiden, Class 4"* — used to separate
  "field absent from the card" from "signal didn't fire in this race".

The pulled HTML is retained in the scratchpad (not committed: ~0.45 MB each of transient
third-party HTML); the durable record is the URLs + date + the count-matrix method in the doc.

**Headline findings written into `docs/racecard-extra-data-audit.md`:**

- **`__NEXT_DATA__` ships in the public/logged-out DOM** in both live pulls, and the full
  structured per-runner soft set is present in it — so issue 001's worry that the fixtures might
  have been captured under a privileged session is **disproved**. Nothing structured is
  members-gated. Availability + Coverage filled for all 18 in-scope rows (row 19 = odds, out of
  scope). `TBD-002` markers cleared.
- **Spotlight** prose is public (full analyst text in the `spotlight` JSON key, sample quoted).
- **Verdict — correction to issue 001:** the prose is in the **rendered `Container__Verdict` DOM**,
  **not** a `__NEXT_DATA__` key (the `verdict` JSON key is **null** in all 5 fixtures + both live
  pulls). Capture = DOM scrape + light NLP, not a cheap JSON read; and it is **not on every card**
  (absent on live Hexham + 3/5 fixtures). Both points handed to 003.
- **Hot-form** signals (`trainerRtf`, trainer win-rate `<sup>`, `newTrainerRacesCount`) are public;
  no dedicated flame flag exists. Coverage gaps for 003: HK card lacks the win-rate `<sup>` and
  `Container__Weather`; wind-surgery skews jumps; several first-time booleans are present as fields
  everywhere but fire only sparsely.
- Brittleness caveats recorded: the `<sup>` classes `sc-25f6462b-7/-9` are build-generated hashes
  (stable 2026-05-20 → 2026-06-21 but rotatable); the odds section only renders when a market is
  open at capture time.

**Notes for issue 003 (now unblocked):** the JSON-read-vs-DOM-scrape split above is direct input
to the Type & parse-difficulty column — most rows are cheap JSON reads, but the **Verdict is the
exception** (DOM + NLP, patchy coverage) and **Spotlight**, though public and JSON-sourced, is free
text so any derived feature is still an NLP problem. Verified no source touched: `git status`
shows only `docs/` + `issues/`.

## Blocked by

- Blocked by `issues/001-offline-inventory-and-parser-diff.md` (needs the candidate inventory
  + the set of ignored hooks to assess against the live DOM).

## User stories addressed

Reference by number from the parent PRD:

- User story 2 (public-DOM availability per candidate)
- User story 3 (coverage across race types: flat vs jumps, GB vs IRE vs HK)
- User story 11 (availability evidence underpinning the soft-set verdicts finalised in 003)
