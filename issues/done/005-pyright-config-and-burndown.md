# Issue 005 — Pyright strict-tuned config + diagnostic burndown

**Type:** AFK

## Parent PRD

`issues/prd.md` — *Type Safety & Static Analysis for the `race_analytics` Python Package*

## What to build

Stage 2 of the rollout: add the type checker and burn the tree down to zero genuine
diagnostics. Deliberately separated from the mechanical reformat (issue 001) so substantive
type fixes are not mixed into the same diff (PRD user story 16).

Concretely:

- Add `[tool.pyright]` to `pyproject.toml` per the PRD's **Pyright configuration**:
  - `typeCheckingMode = "strict"`.
  - Mute the library-`Unknown` family by setting these to `"none"`:
    `reportUnknownMemberType`, `reportUnknownVariableType`, `reportUnknownArgumentType`,
    `reportUnknownLambdaType`, `reportMissingTypeStubs`, `reportMissingTypeArgument`.
    (This is the calibrated decision turning ~1,505 raw strict diagnostics into ~200 genuine
    ones while keeping param/return-annotation discipline and all real-bug rules.)
  - Same strict-tuned mode applied to **both** `race_analytics/` and `tests/` (no looser
    test environment — PRD user story 18).
  - Point pyright at the project venv so imports resolve.
  - Use `[tool.pyright]` in `pyproject.toml` as the single config — do **not** add a
    separate `pyrightconfig.json` (it would silently override the pyproject block).
- Burn down the ~200 genuine diagnostics (`reportArgumentType`, `reportAttributeAccessIssue`,
  `reportCallIssue`, `reportReturnType`, `reportOptionalMemberAccess`, `reportPossiblyUnbound`,
  `reportIndexIssue`, `reportOperatorIssue`, `reportIncompatibleMethodOverride`,
  `reportMissingImports`):
  - Fix genuine bugs **properly**. When a diagnostic reveals a real bug (not a library false
    positive), **first add a focused regression pytest** reproducing it — small in-memory
    DataFrame → call → assert, following `test_data_analysis.py` (PRD Testing Decisions) —
    then fix.
  - Use narrow, rule-specific `# pyright: ignore[rule]` suppressions **only** where a library
    genuinely lies about its types. Blanket `# type: ignore` is disallowed (PRD user story 19).

Do **not** add the pyright pre-commit hook or touch CI / AGENTS.md here — that is issue 006.

## Acceptance criteria

- [ ] `pyproject.toml` has a `[tool.pyright]` block: `typeCheckingMode = "strict"`, the six
      muted `report*` rules set to `"none"`, venv path set, scope covering both
      `race_analytics/` and `tests/`; no `pyrightconfig.json` is added.
- [ ] `pyright` (run against the venv) reports **0** errors across `race_analytics/` and `tests/`.
- [ ] Every `# pyright: ignore[...]` added names a specific rule and corresponds to a genuine
      library typing gap; no blanket `# type: ignore` exists.
- [ ] Any real bug fixed during burndown has a new pytest case reproducing it (added before
      the fix).
- [ ] `python -m pytest tests/` is green (existing behavior + new regression tests).

## Blocked by

- Blocked by `issues/001-adopt-ruff-config-and-reformat.md` (lint-first dead-code removal
  shrinks the type-check surface — PRD user story 17 — and the pinned pyright lives in the
  dev extra added there).

## User stories addressed

- User story 1 (editor squiggles match CLI — completed: Pylance now reads `[tool.pyright]`)
- User story 4 (type checker flags wrong call signatures / `None`-handling at check time)
- User story 9 (no `Unknown`/stub-noise drowning the ~200 real diagnostics)
- User story 10 (strict still forces param/return annotations — coverage ratchets up)
- User story 18 (tests held to the same type bar as the package)
- User story 19 (narrow rule-specific suppressions only for genuine library gaps)
