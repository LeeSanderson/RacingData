# Issue 004 — VS Code editor integration: Ruff

**Type:** HITL

> HITL because it changes the human developer's editor behavior (default formatter +
> format-on-save) and the acceptance signal is verified *in the editor* — format-on-save
> uses Ruff and Pylance squiggles match the CLI. The file edits are trivial; the
> verification is a human-in-VS-Code action.

## Parent PRD

`issues/prd.md` — *Type Safety & Static Analysis for the `race_analytics` Python Package*

## What to build

Make the editor agree with the command-line gate so "clean in the editor" reliably means
"passes the gate" (PRD "Enforcement layers → Editor"). Swap the black-formatter editor
integration for Ruff.

Concretely, in `.vscode/`:

- `settings.json`: change the `[python]` `editor.defaultFormatter` from
  `ms-python.black-formatter` to the Ruff extension (`charliermarsh.ruff`), keeping
  `editor.formatOnSave: true`. Decide and note what to do with the existing
  `notebook.defaultFormatter` / `notebook.formatOnSave.enabled` black references —
  notebooks are out of scope for linting/typing (PRD Out of Scope), so either point them
  at Ruff for consistency or leave them; do not let them keep silently invoking a tool the
  project no longer endorses.
- `extensions.json`: add `charliermarsh.ruff` to `recommendations` (replacing or alongside
  `ms-python.black-formatter`) so opening the project prompts the right extension
  (PRD user story 21).

Pylance already reads `[tool.pyright]` for strict-tuned squiggles once issue 005 lands;
this issue only wires the formatter + recommendations. The same-engine guarantee
(Pylance == pyright CLI) is what makes editor and CLI never disagree (PRD user story 1) —
fully realized once 005 adds the pyright config.

## Acceptance criteria

- [ ] `.vscode/settings.json` `[python]` default formatter is the Ruff extension with
      `formatOnSave` still enabled; the black-formatter reference is removed (or
      consciously retained only for notebooks with a noted reason).
- [ ] `.vscode/extensions.json` recommends `charliermarsh.ruff`.
- [ ] Opening the project in VS Code prompts to install Ruff; saving a Python file formats
      with Ruff (verified in-editor).
- [ ] Editor squiggles match `ruff check` output (and, once 005 lands, `pyright` output).

## Blocked by

- Blocked by `issues/001-adopt-ruff-config-and-reformat.md` (the `[tool.ruff]` config the
  Ruff extension reads must exist).

## User stories addressed

- User story 1 (editor type squiggles match the CLI — partial; completed with 005's pyright config)
- User story 2 (auto-formatting reproducible outside the editor)
- User story 21 (VS Code Ruff extension + recommended-extensions list updated)

## Completion note — 2026-06-17 (done; verified in-editor by Lee)

**Done (committed):**
- `.vscode/settings.json`: `[python]` `editor.defaultFormatter` swapped `ms-python.black-formatter`
  → `charliermarsh.ruff`, `editor.formatOnSave` kept `true`.
- `.vscode/extensions.json`: recommendation `ms-python.black-formatter` → `charliermarsh.ruff`.

**Notebook-formatter decision (the "decide and note" the issue called for):**
- Pointed `notebook.defaultFormatter` at `charliermarsh.ruff` too (rather than leaving the black
  reference), so nothing silently invokes a tool the project no longer endorses. Notebooks are in
  Ruff's `extend-exclude` (`pyproject.toml`), so `ruff format` effectively no-ops on them — which is
  consistent with the PRD treating notebooks as out of scope. The win is that the black reference is
  gone entirely.

**Verified (in-editor, Lee, 2026-06-17):** reload-window picks up the settings; Ruff is the recommended
extension; format-on-save uses Ruff; lint/type squiggles match the CLI (`[tool.pyright]` from 005 is in
place, so Pylance == pyright). All four acceptance criteria met.
