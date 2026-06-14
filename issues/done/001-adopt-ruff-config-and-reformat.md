# Issue 001 — Adopt Ruff: config + pinned dev extra + reformat the tree

**Type:** AFK

## Parent PRD

`issues/prd.md` — *Type Safety & Static Analysis for the `race_analytics` Python Package*

## What to build

The first stage of the PRD's "Staged delivery": adopt Ruff as the project's formatter
**and** linter, pin the dev toolchain, and bring the whole tree to green. This is the
mechanical-reformat slice — deliberately kept separate from any type fixes (PRD user
story 16) so the reformat diff stays reviewable and bisectable.

Touches the Python stage only — no CLI verb, no CSV schema, no `run.ps1` change.

Concretely, in `pyproject.toml`:

- Add a pinned dev dependency group:
  `[project.optional-dependencies] dev = ["ruff==…", "pyright==…", "pre-commit==…", "pytest==…"]`
  (pyright/pre-commit are pinned now even though they are first *used* in 002/005, so the
  one dev extra is the single install for the whole rollout — PRD "Add a pinned dev
  dependency group").
- Add `[tool.ruff]` and `[tool.ruff.lint]` per the PRD's **Ruff configuration**:
  - `select = ["E", "F", "W", "I", "UP", "B", "C4", "SIM", "RUF", "NPY", "PD"]`
    (curated set — explicitly **not** `select = ["ALL"]`).
  - `ignore = ["PD011", "E501"]` (the formatter owns line length; `.values` access is noisy).
  - `target-version = "py310"` (matches `requires-python = ">=3.10"`).
  - Scope: tracked Python in `race_analytics/` and `tests/`.
- **Remove black** as a standalone tool — there is no black dependency pin to drop (it was
  editor-only), but confirm nothing in `pyproject.toml`/docs references it as the canonical
  formatter. (The `.vscode` formatter swap is its own issue, 004.)

Then run `ruff check --fix race_analytics tests` and `ruff format race_analytics tests` and
commit the result. This also clears dead imports / unused vars, shrinking stage 2's type-check
surface (PRD user story 17).

Do **not** add `[tool.pyright]`, the pre-commit config, the CI pipeline, or touch `.vscode`
here — those are issues 002–006.

## Acceptance criteria

- [ ] `pyproject.toml` has `[project.optional-dependencies] dev = [...]` with pinned
      `ruff`, `pyright`, `pre-commit`, `pytest`.
- [ ] `pyproject.toml` has `[tool.ruff]` + `[tool.ruff.lint]` with the curated `select`,
      `ignore = ["PD011", "E501"]`, and `target-version = "py310"`.
- [ ] `pip install -e .[dev]` succeeds in a clean venv.
- [ ] `ruff check race_analytics tests` reports no errors.
- [ ] `ruff format --check race_analytics tests` reports no files would be reformatted.
- [ ] `python -m pytest tests/` is still green (no behavioral regression from the reformat
      or the `--fix` autofixes).
- [ ] No `[tool.pyright]` block, `.pre-commit-config.yaml`, CI pipeline, or `.vscode` change
      is included in this issue's diff.

## Outcome (done 2026-06-14)

Completed. Pinned dev extra (`ruff==0.15.17`, `pyright==1.1.410`, `pre-commit==4.6.0`,
`pytest==9.1.0`) and the curated `[tool.ruff]` / `[tool.ruff.lint]` config added to
`pyproject.toml`. `ruff check --fix` (safe fixes only) + `ruff format` applied, then the
55 non-auto-fixable residuals hand-fixed: `pd.merge(...)` → `.merge(...)` (PD015),
list-concat → unpacking (RUF005), `zip(..., strict=False)` (B905, behaviour-preserving —
`race_count_analysis` zips ragged `bins`/`bins[1:]`, so `strict=True` would have broken
it), `== True`/`== False` → truthiness on the clean-bool `KnownHorseAndJockey` column
(E712), unused-var removal (F841/RUF059), `ClassVar` annotations on test stubs (RUF012),
import consolidation (E402), ambiguous-unicode → ASCII in docstrings (RUF002). Three
`# noqa` total — all `B024`/`B027` on `features/base.RaceDataProcessor`, an intentional
template-method base whose hooks are optional no-ops (decorating `@abstractmethod` would
be a contract change, out of scope for the mechanical slice).

**Deviation from the literal config spec:** added
`extend-exclude = ["race_analytics/notebooks"]` to `[tool.ruff]`. The tracked `*.ipynb`
notebooks (and their gitignored nbconvert `*.py`) live under `race_analytics/`, and the
acceptance command `ruff check race_analytics` would otherwise scan them — but the PRD
puts notebooks explicitly out of scope ("not linted/typed/formatted"). The exclude makes
ruff's scope match the PRD.

Verified: `pip install -e .[dev]` succeeds; `ruff check race_analytics tests` → "All
checks passed!"; `ruff format --check` → 86 files already formatted; `pytest tests/` →
420 passed (unchanged from baseline). No `[tool.pyright]`, `.pre-commit-config.yaml`, CI
YAML, or `.vscode` change in the diff.

## Blocked by

None — can start immediately.

## User stories addressed

- User story 5 (dead imports / unused vars / undefined names caught)
- User story 6 (deprecated numpy/pandas patterns — NPY/PD rules)
- User story 7 (syntax modernized to `py310` — UP rules)
- User story 8 (bug-prone patterns — bugbear B rules)
- User story 11 (all tool config in `pyproject.toml`)
- User story 12 (dev tool versions pinned)
- User story 17 (lint pass runs first, shrinking stage 2's surface)
