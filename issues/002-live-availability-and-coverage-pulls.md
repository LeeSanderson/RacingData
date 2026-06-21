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

- [ ] The doc's **Method** section records the two live-pull dates and the two meeting/race
      types (flat handicap + jumps), OR an explicit caveat that live pulls were unavailable and
      the audit fell back to the 5 fixtures.
- [ ] Every candidate row from issue 001 has a **public-DOM availability** value
      (present / members-only / absent), justified by the live pulls and/or fixtures.
- [ ] Every candidate row has a **coverage across corpus** value that calls out flat-vs-jumps
      and GB-vs-international gaps where they exist.
- [ ] The soft set specifically (Spotlight, RP verdict, hot-trainer/jockey badges) has its
      public-vs-members-only status resolved (or marked "unable to determine" with reason).
- [ ] No C# / Python source files are modified (`git status` shows only `docs/`, `issues/`, and
      any saved-HTML/scratch artefacts).

## Blocked by

- Blocked by `issues/001-offline-inventory-and-parser-diff.md` (needs the candidate inventory
  + the set of ignored hooks to assess against the live DOM).

## User stories addressed

Reference by number from the parent PRD:

- User story 2 (public-DOM availability per candidate)
- User story 3 (coverage across race types: flat vs jumps, GB vs IRE vs HK)
- User story 11 (availability evidence underpinning the soft-set verdicts finalised in 003)
