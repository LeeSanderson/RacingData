# PRD: Type Safety & Static Analysis for the `race_analytics` Python Package

> **Nature of this PRD:** This is a tooling/infrastructure change to the **Python stage only**. It adds no CLI verb, no CSV schema change, and no new data step to `run.ps1`. It does add a new CI pipeline and a commit-time gate. The C#/.NET stage is untouched.

## Problem Statement

The Python package `race_analytics` (~41 source files, pandas/numpy/sklearn/xgboost-heavy) has grown to carry the production prediction pipeline, but it has no enforced code-quality floor:

- **Type safety is partial and unenforced.** `algorithms/base.py` is fully typed (Protocols, `ClassVar`, return types), but most other modules carry only 1–3 annotated defs. Nothing checks them. A type error — a wrong call signature, a `None` that shouldn't be, a renamed column attribute — is only caught when code runs (or worse, when it silently produces wrong predictions).
- **Formatting is editor-only and invisible to automation.** Black runs via the VS Code extension with format-on-save, but it is **not pinned in `pyproject.toml` or the dependencies**. Claude/AI agents and any non-VS-Code context don't know it exists, so formatting is inconsistent and unreproducible.
- **There is no static analysis.** Dead imports, undefined names, deprecated pandas/numpy patterns, and refactor-able anti-patterns accumulate unchecked.
- **There is no gate.** The only Azure DevOps pipeline is a scheduled 6 AM data-refresh job (`trigger: none, pr: none`). Nothing runs lint/types/tests on a change before it lands on `main`.

Both human (Lee, via VS Code) and AI (Claude, via the `work-on-next-issue` / `/loop` AFK queues) work this codebase. Today neither gets a consistent, automated signal about code health.

## Solution

Adopt a consolidated, pinned, gated quality toolchain for the Python package, where the **editor and the command line agree** and there is **one command** every actor runs:

- **Ruff** for both formatting (`ruff format`, replacing black — black-compatible output, near-zero reformat churn) and linting (a curated broad rule set).
- **Pyright** for type checking — deliberately chosen because it is the *same engine* as Lee's VS Code Pylance, so editor squiggles and CLI errors never disagree. Run in **strict mode with the pandas/numpy "no-stubs → `Unknown`" noise family muted**, which (measured) reduces the diagnostic load from **1,505 to ~200 genuine type issues** while keeping strict's discipline on the project's own code and every real-bug rule.
- **One gate command:** `pre-commit run --all-files` defines the ruff + ruff-format + pyright checks once; humans, AI agents, the pre-commit hook, and CI all invoke the same thing. No definition drift.
- **Four enforcement layers:** editor integration (human), an AGENTS.md verification-loop rule (AI), a pre-commit hook (local + AFK loops), and a new Azure DevOps CI pipeline (durable safety net on push-to-`main` / PR).

Delivered in **two stages** matching the issue-queue workflow: format+lint first (fast green, also clears dead code), then type checking (burn down the ~200 diagnostics).

## User Stories

1. As a human developer in VS Code, I want my editor's type squiggles to match exactly what the command-line checker reports, so that "clean in the editor" reliably means "passes the gate."
2. As a human developer, I want auto-formatting to be reproducible outside my editor, so that a teammate or AI agent produces identically-formatted code without my VS Code settings.
3. As an AI agent working an AFK issue, I want a single documented command to verify code health before committing, so that I never push lint/type/format regressions onto `main`.
4. As an AI agent, I want the type checker to flag a wrong call signature or a `None`-handling bug at check time, so that I catch the error before it reaches the prediction pipeline and corrupts results.
5. As a maintainer, I want dead imports, unused variables, and undefined names caught automatically, so that the codebase stays navigable for both human and AI readers.
6. As a maintainer, I want deprecated numpy/pandas patterns flagged (NPY/PD rules), so that the code keeps working across the pinned pandas 3.x / numpy 2.x upgrades already installed.
7. As a maintainer, I want syntax modernized to the project's `py310` floor (UP rules), so that the code uses current idioms consistently.
8. As a maintainer, I want bug-prone patterns (mutable default args, etc. — bugbear rules) flagged, so that latent bugs surface during review rather than in production.
9. As a developer touching pandas-heavy code, I want the type checker to **not** drown me in "this DataFrame method returned `Unknown`" noise, so that the ~200 real diagnostics aren't buried under ~1,250 library-stub false positives.
10. As a developer, I want strict mode to still force me to annotate the parameters and return types of new functions, so that the package's type coverage ratchets upward over time instead of decaying.
11. As a developer, I want all tool configuration in a single file (`pyproject.toml`), so that the editor, CLI, pre-commit, and CI all read one source of truth.
12. As a developer, I want the dev tool versions pinned, so that the gate behaves identically on my machine, in CI, and in any AI agent's environment.
13. As a maintainer with no PR gate today, I want a CI pipeline that runs the quality checks and tests on every push to `main`, so that a forgotten local check is still caught.
14. As a developer running an AFK `/loop`, I want a commit-time pre-commit hook, so that an agent cannot commit red code even if its prompt forgets to run the check.
15. As a developer, I want the pre-commit type-check hook to resolve the installed pandas/numpy, so that it reports real diagnostics instead of a flood of "missing import" false positives.
16. As a maintainer, I want the rollout staged into two reviewable issues, so that mechanical reformatting is not mixed into the same diff as substantive type fixes (clean bisects, easier review).
17. As a maintainer, I want the linter pass to run first, so that dead-code removal shrinks the type checker's surface before stage 2.
18. As a developer, I want tests held to the same type bar as the package, so that test helpers and fixtures stay type-correct and don't silently rot.
19. As a developer, I want narrow, rule-specific suppressions (`# pyright: ignore[rule]`) only where a library genuinely lies about its types, so that suppressions document a real reason rather than blanket-hiding errors.
20. As an AI agent reading AGENTS.md, I want the quality gate wired into the documented "After Python changes" verification loop, so that running it is part of my standard procedure, not an afterthought.
21. As a human developer, I want the VS Code setup (Ruff extension, recommended-extensions list) updated in the repo, so that opening the project prompts the right tooling automatically.
22. As a maintainer, I want the scheduled 6 AM data-refresh pipeline left untouched, so that adding CI doesn't risk the daily production data update.

## Implementation Decisions

**Toolchain**
- Adopt **Ruff** as both formatter and linter; **remove black** as a standalone tool/dependency. `ruff format` output is black-compatible, so the one-time reformat is minimal churn.
- Adopt **pyright** as the type checker (not mypy), because it is the same engine as the existing Pylance editor experience — editor and CLI cannot disagree. (Astral's `ty` considered and deferred: pre-1.0 as of this PRD; revisitable later since Ruff is already adopted.)

**Ruff configuration** (in `pyproject.toml`)
- Curated broad rule set: `E, F, W, I, UP, B, C4, SIM, RUF, NPY, PD`. (Explicitly *not* `select = ["ALL"]` — avoids conflicting/opinionated families and an ongoing ignore-list chore.)
- Disable the known-noisy rules: `PD011` (`.values` access) and `E501` (line length — the formatter owns wrapping).
- `target-version = "py310"` (matches `requires-python = ">=3.10"`).
- Scope: all tracked Python (`race_analytics/` + `tests/`).

**Pyright configuration** (in `pyproject.toml` under `[tool.pyright]`)
- `typeCheckingMode = "strict"`.
- **Mute the library-`Unknown` family** by setting these to `"none"`: `reportUnknownMemberType`, `reportUnknownVariableType`, `reportUnknownArgumentType`, `reportUnknownLambdaType`, `reportMissingTypeStubs`, `reportMissingTypeArgument`. This is the calibrated decision that turns 1,505 raw strict diagnostics into ~200 genuine ones while preserving param/return-annotation discipline and all real-bug rules.
- Same strict-tuned mode applied to **both `race_analytics/` and `tests/`** (no looser test environment).
- Point pyright at the project venv so imports resolve.
- Use `[tool.pyright]` in `pyproject.toml` as the single config — **do not** add a separate `pyrightconfig.json` (its presence would silently override the pyproject block).

**Config & dependency location**
- All tool config consolidated in `pyproject.toml` (`[tool.ruff]`, `[tool.ruff.lint]`, `[tool.pyright]`) — one source of truth read by the editor (Pylance), CLI, pre-commit, and CI.
- Add a pinned dev dependency group: `[project.optional-dependencies] dev = [ruff, pyright, pre-commit, pytest]` with version pins.

**The single gate command**
- `pre-commit run --all-files` is *the* quality gate, defining the ruff-lint + ruff-format + pyright checks once. Humans, AI agents, the commit hook, and CI all call it — eliminating definition drift.
- The test suite (`python -m pytest tests/`) stays a separate step (too slow for a commit hook); it remains the existing behavioral verification.

**Enforcement layers**
- **Editor:** swap the `[python]` default formatter in `.vscode/settings.json` from the black-formatter extension to the **Ruff extension** (format-on-save + lint); add Ruff to `.vscode/extensions.json` recommendations. Pylance reads `[tool.pyright]` for strict-tuned squiggles.
- **AGENTS.md:** add the gate command to the "After Python changes" verification loop and note the Ruff/pyright conventions, so AFK agents run it before committing.
- **pre-commit hook:** a new `.pre-commit-config.yaml` with ruff + ruff-format hooks, and a pyright hook configured as a `repo: local` / system hook running the venv's pyright (so installed pandas/numpy resolve — avoids the isolated-env missing-import trap).
- **CI:** a new Azure DevOps pipeline (separate from the scheduled data job) triggered on push-to-`main` (and PRs if branching is ever used): set up Python → `pip install -e .[dev]` → `pre-commit run --all-files` → `python -m pytest tests/`. The existing scheduled 6 AM data-refresh pipeline is left untouched.

**Staged delivery**
- **Issue 1 — Format + Lint:** add the dev extra and Ruff config; run `ruff check --fix` and `ruff format`; wire the pre-commit hook and CI pipeline for Ruff only. Reaches green fast and removes dead imports/vars (shrinking stage 2's noise).
- **Issue 2 — Type checking:** add `[tool.pyright]`; burn down the ~200 diagnostics (fix genuine bugs properly; narrow `# pyright: ignore[rule]` only for true library false positives); add pyright to the pre-commit hook and CI; update AGENTS.md.

**Measured baseline (from probing the live code)**
- Pyright standard mode: 199 diagnostics. Strict mode: 1,505. Of strict's, ~1,250 are library-`Unknown`/missing-stub noise; ~200 are real (`reportArgumentType`, `reportAttributeAccessIssue`, `reportCallIssue`, `reportReturnType`, `reportOptionalMemberAccess`, `reportPossiblyUnbound`, `reportIndexIssue`, `reportOperatorIssue`, `reportIncompatibleMethodOverride`, `reportMissingImports`). The muted-strict config targets exactly that ~200.

## Testing Decisions

- **What "tested" means here:** This PRD adds tooling, not pipeline behavior. The primary acceptance signal is that **`pre-commit run --all-files` is green** and **CI passes** (gate + existing `pytest` suite), on a clean checkout, for both stages.
- **No new unit tests for configuration.** Config files are verified by the gate running green, not by pytest assertions.
- **Existing behavior must not regress:** the full `python -m pytest tests/` suite must stay green throughout both stages. The Python side already has meaningful pytest coverage (`tests/` mirrors the package: `tests/algorithms/`, `tests/features/`, `tests/scripts/`, `tests/utils/`) — this is the regression backstop.
- **Real bugs surfaced by the type checker get regression tests.** If burning down the ~200 diagnostics in Issue 2 uncovers a genuine bug (not a library false positive), add a focused pytest case reproducing it before fixing — following the existing pattern (small in-memory DataFrame → call → assert, as in `test_data_analysis.py`).
- **Suppressions are reviewed, not rubber-stamped.** Every `# pyright: ignore[rule]` added in Issue 2 must name a specific rule and correspond to a genuine library typing gap; blanket `# type: ignore` is disallowed.
- **CI is the durable test of the gate itself:** the new pipeline running green on push-to-`main` proves the gate works outside any one developer's machine.

## Out of Scope

- The **C#/.NET stage** (`RacePredictor.Core`, `RaceDataDownloader`, their tests) — it has its own analyzers/`.DotSettings` and rich xUnit+Verify coverage; no changes here.
- **Notebooks** — none are tracked in source control, and the nbconvert `*.py` outputs (`race_analytics/notebooks/*.py`, `Data/*.py`) are gitignored, so they are not linted/typed/formatted.
- **Deep DataFrame/Series typing** (e.g. column-level typed schemas, pandera, full pandas-stubs adoption) — explicitly avoided; pandas is treated as loosely typed via the muted `Unknown` rules.
- **mypy / ty** — not adopted; pyright is the single type checker. `ty` may be revisited post-1.0.
- **Switching the team to a PR-based branch workflow** — CI is wired for the current push-to-`main` reality (with PR triggers ready if branching is later adopted), but the workflow change itself is not part of this PRD.
- **The scheduled 6 AM data-refresh pipeline** — left exactly as-is.

## Further Notes

- The `pre-commit run --all-files` decision is the one architectural choice made on the user's behalf (vs. a separate `checks.ps1`): it guarantees zero drift between the local, AI, and CI definitions of the gate, at the cost of routing the gate through the pre-commit framework.
- The pyright pre-commit hook **must** be a local/system hook (not pre-commit's default isolated environment) so it sees the installed scientific stack; a misconfigured isolated hook would report spurious missing-import errors and undermine trust in the gate.
- A stubborn pyright false positive can block an autonomous `/loop` commit. The mitigation is narrow `# pyright: ignore[rule]` suppressions for genuine library gaps — accepted as the cost of the AFK-loop safety guarantee.
- The diagnostic counts (199 / 1,505 / ~200) were measured against the current tree; they may shift slightly after Issue 1's dead-code cleanup, which only helps.
