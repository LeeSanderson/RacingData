# Issue 002 — Local gate: pre-commit hook (ruff + ruff-format)

**Type:** AFK

## Parent PRD

`issues/prd.md` — *Type Safety & Static Analysis for the `race_analytics` Python Package*

## What to build

Stand up the **single gate command** for the local + AFK-loop layer: a
`.pre-commit-config.yaml` that defines the ruff-lint and ruff-format checks once, so a
commit (human or autonomous `/loop`) cannot land red-by-ruff code. Per the PRD's "single
gate command" decision, `pre-commit run --all-files` becomes *the* quality gate that humans,
AI agents, the commit hook, and (later) CI all invoke — no definition drift.

Scope of this issue — ruff only. Pyright is added to the same config later in issue 006.

Concretely:

- Add `.pre-commit-config.yaml` with the upstream `astral-sh/ruff-pre-commit` hooks:
  - `ruff` (lint) — with `--fix` matching the issue-001 behavior, or check-only; keep
    consistent with the PRD's "ruff-lint + ruff-format" gate.
  - `ruff-format`.
  - Pin the hook `rev` to match the `ruff` version pinned in the dev extra (001) so the
    hook and the CLI agree.
- Run `pre-commit install` so the hook fires on `git commit` locally and in AFK loops.

The test suite stays a **separate** step (`python -m pytest tests/`) — too slow for a commit
hook (PRD "The single gate command").

## Acceptance criteria

- [ ] `.pre-commit-config.yaml` exists with `ruff` + `ruff-format` hooks, `rev` pinned to
      the dev-extra ruff version.
- [ ] `pre-commit run --all-files` exits 0 (tree is already ruff-clean from issue 001).
- [ ] A deliberately mis-formatted / lint-violating staged change is blocked by
      `git commit` (hook fires), and a clean change commits.
- [ ] `python -m pytest tests/` is unaffected (not run by the hook).

## Blocked by

- Blocked by `issues/001-adopt-ruff-config-and-reformat.md` (needs the pinned ruff version
  and a ruff-clean tree for the hook to pass).

## User stories addressed

- User story 3 (single documented command to verify code health before committing — partial; completed in 006)
- User story 14 (commit-time pre-commit hook so an AFK agent cannot commit red code)
