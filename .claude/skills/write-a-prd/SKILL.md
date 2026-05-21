---
name: write-a-prd
description: Generate a PRD from the client brief and write it as a local markdown file in issues/. Use when the user wants to turn a client request into a structured PRD.
---

This skill will be invoked when the user wants to create a PRD. You may skip steps if you don't consider them necessary.

## Project context

PRDs in this repo describe changes to the two-stage racing-data pipeline:

- C# extraction stage (`RacePredictor.Core`, `RaceDataDownloader`) — domain models, parsers, command handlers under `RaceDataDownloader/Commands/<Verb>/`.
- Python ML stage (`Data/*.py`) — feature engineering and linear-regression prediction over CSVs produced by the C# stage.

The PRD lives at `issues/prd.md`. Vertical-slice issues that break it down live alongside as `issues/NNN-*.md`.

## Process

1. Ask the user for a long, detailed description of the problem they want to solve and any potential ideas for solutions.

2. Explore the repo to verify their assertions and understand the current state of the codebase — typically: which CLI verbs exist (`updateresults`, `downloadresults`, `todaysracecards`, `validate`, `dedupe`, `fixraceids`, `downloadracecards`), what columns the relevant CSVs already carry, and which Python script(s) would be touched.

3. Interview the user relentlessly about every aspect of this plan until you reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. Useful branches in this codebase: which CLI verb (new or extended)? which CSV schema changes? which Python script consumes the change? how does it ride through `run.ps1`?

4. Sketch out the major modules you will need to build or modify to complete the implementation. Actively look for opportunities to extract deep modules that can be tested in isolation.

A deep module (as opposed to a shallow module) is one which encapsulates a lot of functionality in a simple, testable interface which rarely changes. Existing examples: `RacingResultParser.Parse`, `IRacingDataDownloader`, `UpdateResultsCommandHandler.RunAsync`.

Check with the user that these modules match their expectations. Check with the user which modules they want tests written for (note: the C# side has rich test coverage via xUnit + Verify; the Python side typically does not — flag this as a gap if the PRD touches `Data/`).

5. Once you have a complete understanding of the problem and solution, use the template below to write the PRD. The PRD should be written as a local markdown file at `issues/prd.md`. Create the `issues/` directory if it doesn't exist. Do NOT submit a GitHub issue or call any external service.

<prd-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, numbered list of user stories. Each user story should be in the format of:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a punter using TodaysPredictions.csv, I want jockey win-rate to influence the predicted finish position, so that I can spot value that the current model misses
</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature.

## Implementation Decisions

A list of implementation decisions that were made. This can include:

- The modules that will be built/modified (e.g. a new command handler under `RaceDataDownloader/Commands/`, a change to `JockeyStatsBuilder.py`, a new column in `Race_Features.csv`)
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions (e.g. ports & adapters around a new external source)
- Schema changes (CSV columns added/renamed; note that monthly `Results_YYYYMM.csv` files are append-only in spirit)
- API contracts (e.g. the shape of `Predictions.json` / `TodaysPredictions.csv`)
- Specific interactions (how `run.ps1` wires the new step in)

Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

## Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details — drive command handlers via `RunAsync` and assert on the CSV produced)
- Which modules will be tested
- Prior art for the tests (e.g. `UpdateResultsCommandHandlerShould`, `ValidateRaceCardPredictionsCommandHandlerShould`, parser tests in `RacePredictor.Core.Tests` using `FakeData.*` fixture HTML)
- For Python changes: whether new pure functions will be extracted to allow pytest-style testing, or whether the change is verified only via `.\run.ps1` output

## Out of Scope

A description of the things that are out of scope for this PRD.

## Further Notes

Any further notes about the feature.

</prd-template>
