---
name: prd-to-issues
description: Break a PRD into independently-workable issues and write each as a local markdown file in issues/. Use when the user wants to turn a PRD into a list of concrete tasks.
---

# PRD to Issues

Break a PRD into independently-grabbable issues using vertical slices (tracer bullets), written as local markdown files under `issues/`.

## Project context

In this codebase a "vertical slice" usually cuts across the C# stage **and** the Python stage:

- C# side: a new/changed command handler under `RaceDataDownloader/Commands/<Verb>/`, possibly new domain types in `RacePredictor.Core`, paired tests in `RaceDataDownloader.Tests` / `RacePredictor.Core.Tests` (xUnit + Verify snapshots).
- CSV schema: any new columns in `Results_YYYYMM.csv`, `Race_Features.csv`, `Horse_Stats.csv`, etc.
- Python side: matching changes to the relevant script under `Data/` (`FeatureAnalysis`, `HorseStatsBuilder`, `JockeyStatsBuilder`, `LinearRegressionPredictor`).
- Pipeline glue: `run.ps1` wiring if a new verb or step is introduced.

A complete slice is verifiable by running `.\run.ps1` (or a focused subset of it) and seeing the new behavior produce the expected file output.

## Process

### 1. Locate the PRD

Ask the user for the PRD file path (e.g. `issues/prd.md`).

If the PRD is not already in your context window, read it from the file.

### 2. Explore the codebase (optional)

If you have not already explored the codebase, do so to understand the current state of the code — especially the existing verbs in `RaceDataDownloader/Commands/`, the CSV schemas they produce, and which `Data/*.py` scripts consume those CSVs.

### 3. Draft vertical slices

Break the PRD into **tracer bullet** issues. Each issue is a thin vertical slice that cuts through ALL integration layers end-to-end, NOT a horizontal slice of one layer.

Slices may be 'HITL' or 'AFK'. HITL slices require human interaction, such as an architectural decision or a design review. AFK slices can be implemented and merged without human interaction. Prefer AFK over HITL where possible.

<vertical-slice-rules>
- Each slice delivers a narrow but COMPLETE path through every relevant layer (C# handler + tests, CSV schema, Python consumer if any, `run.ps1` wiring)
- A completed slice is demoable on its own — running the affected verb or `.\run.ps1` produces a visibly different file
- Prefer many thin slices over few thick ones (e.g. "add JockeyId to RaceCardRecord" before "use JockeyId in LinearRegressionPredictor")
</vertical-slice-rules>

### 4. Quiz the user

Present the proposed breakdown as a numbered list. For each slice, show:

- **Title**: short descriptive name
- **Type**: HITL / AFK
- **Blocked by**: which other slices (if any) must complete first
- **User stories covered**: which user stories from the PRD this addresses

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the dependency relationships correct? (e.g. does the Python feature change actually need the C# schema change to land first?)
- Should any slices be merged or split further?
- Are the correct slices marked as HITL and AFK?

Iterate until the user approves the breakdown.

### 5. Create the issue files

For each approved slice, write a markdown file in `issues/` using the naming pattern `issues/NNN-short-title.md` (e.g. `issues/004-add-jockey-id-to-racecard-record.md`).

Number issues starting from the next available number (check what files already exist in `issues/`).

Create files in dependency order (blockers first) so you can reference real filenames in the "Blocked by" field.

Do NOT use `gh issue create` or any GitHub CLI commands. Do NOT reference GitHub issue numbers. Use local filenames for all cross-references.

<issue-template>
## Parent PRD

`issues/prd.md` (or whichever PRD file was used)

## What to build

A concise description of this vertical slice. Describe the end-to-end behavior, not layer-by-layer implementation. Reference specific sections of the parent PRD rather than duplicating content. If the slice touches both the C# and Python halves, name the verb / script affected.

## Acceptance criteria

- [ ] Criterion 1 (e.g. `RaceDataDownloader.exe <verb> --output Data` produces a CSV with column X)
- [ ] Criterion 2 (e.g. the matching `*.Tests` project has a new `Should` test asserting on the Verify snapshot)
- [ ] Criterion 3 (e.g. `Data/<Script>.py` reads/writes the new column without erroring on existing fixture data)

## Blocked by

- Blocked by `issues/NNN-title.md` (if any)

Or "None - can start immediately" if no blockers.

## User stories addressed

Reference by number from the parent PRD:

- User story 3
- User story 7

</issue-template>

Do NOT close or modify the parent PRD file.
