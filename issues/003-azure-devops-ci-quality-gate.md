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

- Add `.azuredevops/quality-checks.yml` (a new file alongside, not replacing,
  `scheduled-run.yml`):
  - `trigger: main` (push-to-`main`); add a `pr` trigger too so it is ready if a branch
    workflow is ever adopted (PRD "triggered on push-to-`main` (and PRs if branching is
    ever used)").
  - `pool: vmImage: 'windows-latest'` (consistent with the repo's existing pipeline).
  - Steps: set up Python → `pip install -e .[dev]` → `pre-commit run --all-files` →
    `python -m pytest tests/`.
- **Register** the pipeline in Azure DevOps and confirm it runs green on `main`.
- Leave `.azuredevops/scheduled-run.yml` (the 6 AM `trigger: none, pr: none` data-refresh
  job) **exactly as-is** (PRD user story 22 / Out of Scope).

At this stage the gate (`pre-commit run --all-files`) only runs ruff (pyright is added to
the pre-commit config in 006, at which point CI picks it up automatically — no CI change
needed then).

## Acceptance criteria

- [ ] `.azuredevops/quality-checks.yml` exists, triggers on push-to-`main`, installs
      `-e .[dev]`, runs `pre-commit run --all-files`, then `python -m pytest tests/`.
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
