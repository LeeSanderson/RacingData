# Issue 003 — CI: new Azure DevOps quality-gate pipeline

**Type:** HITL

> HITL because registering a new pipeline in the Azure DevOps portal (New Pipeline →
> point at the YAML, authorize the agent pool / service connection) and confirming a
> green run are actions only a human with portal access can perform. The YAML authoring
> is mechanical; the registration + verification is not.

## Parent PRD

`issues/prd.md` — *Type Safety & Static Analysis for the `race_analytics` Python Package*

## What to build

A **new** Azure DevOps pipeline, separate from the existing scheduled data job, that runs
the quality gate + the test suite on every push to `main` (PRD user story 13). It is the
durable safety net: a forgotten local check is still caught.

Concretely:

- Add `.azuredevops/ci.yml` (a new file alongside, not replacing, `scheduled-run.yml`).
  Originally authored as `quality-checks.yml`; renamed to `ci.yml` when the C# job was
  added (see the 2026-06-16 note) since it now covers more than the Python gate:
  - `trigger: main` (push-to-`main`); add a `pr` trigger too so it is ready if a branch
    workflow is ever adopted (PRD "triggered on push-to-`main` (and PRs if branching is
    ever used)").
  - `pool: vmImage: 'windows-latest'` (consistent with the repo's existing pipeline).
  - Two parallel jobs:
    - `python` — set up Python → `pip install -e .[dev]` → `pre-commit run --all-files` →
      `python -m pytest tests/`.
    - `csharp` — set up .NET 9 → `dotnet build` → `dotnet test` (Debug, matching the local
      `dotnet build && dotnet test` loop); publishes TRX results + Cobertura coverage.
      Build + test only by design — no `dotnet format`/analyzer gate.
- **Register** the pipeline in Azure DevOps and confirm it runs green on `main`.
- Leave `.azuredevops/scheduled-run.yml` (the 6 AM `trigger: none, pr: none` data-refresh
  job) **exactly as-is** (PRD user story 22 / Out of Scope).

At this stage the gate (`pre-commit run --all-files`) only runs ruff (pyright is added to
the pre-commit config in 006, at which point CI picks it up automatically — no CI change
needed then).

## Acceptance criteria

- [ ] `.azuredevops/ci.yml` exists, triggers on push-to-`main`, with a `python` job that
      installs `-e .[dev]`, runs `pre-commit run --all-files`, then `python -m pytest tests/`.
- [ ] `.azuredevops/ci.yml` has a `csharp` job that runs `dotnet build` + `dotnet test`
      (Debug) on .NET 9 and publishes test results + coverage.
- [ ] The pipeline is registered in Azure DevOps and has at least one **green** run on `main`.
- [ ] `.azuredevops/scheduled-run.yml` is byte-for-byte unchanged.
- [ ] The new pipeline does not interfere with the scheduled 6 AM run (separate pipeline,
      separate trigger).

## Blocked by

- Blocked by `issues/002-pre-commit-hook-ruff.md` (CI invokes `pre-commit run --all-files`,
  which requires `.pre-commit-config.yaml` to exist).

## User stories addressed

- User story 13 (CI pipeline runs quality checks + tests on every push to `main`)
- User story 22 (scheduled 6 AM data-refresh pipeline left untouched)

## Progress note — 2026-06-14 (mechanical YAML slice done; portal steps remain)

The AFK-doable part is committed; the two human-only acceptance criteria remain for Lee.

**Done (committed):**
- `.azuredevops/quality-checks.yml` authored: `trigger: [main]` + `pr: [main]`,
  `pool: vmImage: 'windows-latest'`, steps `UsePythonVersion@0 (3.12)` →
  `pip install -e ".[dev]"` → `pre-commit run --all-files` → `python -m pytest tests/`.
  Uses the default self-checkout (unlike `scheduled-run.yml`, which clones manually to
  push back). `.[dev]` is quoted so PowerShell doesn't glob the `[dev]` extra.
- `.azuredevops/scheduled-run.yml` left byte-for-byte unchanged (verified via git status).
- Locally ran the exact CI steps to de-risk the first run: gate
  `pre-commit run --all-files` → ruff + ruff-format + pyright (strict, venv) all Passed;
  `python -m pytest tests/` → 422 passed. Both YAML files parse.
- NOTE: 006 already added pyright to the pre-commit config, so the gate this pipeline
  invokes runs ruff **and** pyright now (the issue's "ruff only at this stage" note
  assumed 003 landed before 006; CI just invokes the gate command, so order is moot).

**Remaining (HITL — Lee, via the Azure DevOps portal):**
- [ ] Register the pipeline: New Pipeline → GitHub → point at `.azuredevops/ci.yml`
      → authorize the agent pool / GitHub service connection.
- [ ] Confirm at least one **green** run on `main` (both the `python` and `csharp` jobs).

Once the green run is confirmed, move this file to `issues/done/`.

## Progress note — 2026-06-16 (extended to C# + renamed to ci.yml)

The mechanical part of the C# extension is committed; the HITL registration step above
still remains (now pointing at `ci.yml`).

**Done (committed):**
- Renamed `.azuredevops/quality-checks.yml` → `.azuredevops/ci.yml` via `git mv` (history
  preserved). The pipeline was not yet registered in the portal, so the rename needed no
  portal change — just register New Pipeline against `ci.yml` when doing the HITL step.
- Restructured the single flat `steps:` list into two parallel `jobs:` (both inherit the
  top-level `pool: windows-latest`):
  - `python` — the existing gate + pytest, unchanged in substance.
  - `csharp` — `UseDotNet@2` (`9.0.x`) → `dotnet build RacePredictor.sln` (Debug) →
    `dotnet test --no-build --logger trx --collect "XPlat Code Coverage"` →
    `PublishTestResults@2` + `PublishCodeCoverageResults@2` (both `succeededOrFailed()`).
  - C# is **build + test only** — no `dotnet format`/`-warnaserror` gate (the `.editorconfig`
    analyzers stay at `warning`). Low risk of an initial red run: `scheduled-run.yml`
    already runs `dotnet build && dotnet test` daily on the same SDK/config.
- `.azuredevops/scheduled-run.yml` left byte-for-byte unchanged.
- Added a one-line note to AGENTS.md ("After C# changes") that the same build+test runs
  in CI.
