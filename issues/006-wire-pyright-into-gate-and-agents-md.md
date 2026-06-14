# Issue 006 — Wire pyright into the gate + AGENTS.md

**Type:** AFK

## Parent PRD

`issues/prd.md` — *Type Safety & Static Analysis for the `race_analytics` Python Package*

## What to build

Close the loop on stage 2: make pyright part of the **single gate command** so every actor
(human, AI agent, commit hook, CI) runs it via the same `pre-commit run --all-files`, and
document the gate so AFK agents run it as standard procedure.

Concretely:

- Add a pyright hook to `.pre-commit-config.yaml` as a `repo: local` / `system` hook that
  invokes the **venv's** pyright (not pre-commit's default isolated environment). This is
  required so the installed pandas/numpy resolve — a misconfigured isolated hook would
  report spurious missing-import errors and undermine trust in the gate (PRD user story 15
  and the "Further Notes" warning).
- No CI YAML change needed: the pipeline from issue 003 already runs
  `pre-commit run --all-files`, so it picks up the new pyright hook automatically.
- Update `AGENTS.md`:
  - Add the gate command (`pre-commit run --all-files`) to the **"After Python changes"**
    verification loop so AFK agents run it before committing (PRD user story 20).
  - Note the Ruff (formatter + linter) / pyright (strict-tuned) conventions and the
    narrow-`# pyright: ignore[rule]`-only suppression rule.

This issue also realizes the staged-delivery intent (PRD user story 16): stage 1 (issues
001–004) was mechanical reformat + ruff enforcement; stage 2 (005–006) is the type-fix work,
kept in a separate diff.

## Acceptance criteria

- [ ] `.pre-commit-config.yaml` has a pyright hook configured as `repo: local` / system,
      running the venv pyright (resolves the installed pandas/numpy — no spurious
      missing-import diagnostics).
- [ ] `pre-commit run --all-files` exits 0 with all hooks (ruff, ruff-format, **pyright**)
      enabled.
- [ ] The Azure DevOps pipeline (issue 003) re-runs green on `main` with pyright now in the
      gate (no YAML edit required).
- [ ] `AGENTS.md` "After Python changes" loop documents `pre-commit run --all-files` and the
      Ruff/pyright conventions + suppression rule.
- [ ] `python -m pytest tests/` remains green.

## Blocked by

- Blocked by `issues/002-pre-commit-hook-ruff.md` (extends the existing `.pre-commit-config.yaml`).
- Blocked by `issues/005-pyright-config-and-burndown.md` (needs `[tool.pyright]` and a
  pyright-clean tree so the new hook passes).

## User stories addressed

- User story 3 (single documented command to verify code health — completed)
- User story 15 (pre-commit pyright hook resolves the installed pandas/numpy)
- User story 16 (rollout staged into two reviewable issues)
- User story 20 (quality gate wired into the AGENTS.md "After Python changes" loop)
