# Move staking-summary logic into `betting`; slim `backtest_staking.py` to a CLI wrapper

## Parent PRD

`issues/prd.md` — "Kelly-staked ROI in the evaluation metrics"

## What to build

The single-source-of-truth refactor that every later slice depends on. Move the four
summary helpers that currently live privately in
`race_analytics/scripts/backtest_staking.py` —
`_attach_stakes`, `_identify_picks`, `_summarise`, `_backtest` (plus the supporting
`_empty_summary` and the `_STAKE` / `_STAKING_INPUTS` / `_STAKE_DIST_FIELDS` constants) —
into `race_analytics/betting/staking.py` as **public, pure** functions, and re-export them
from the `betting` package's public surface in `race_analytics/betting/__init__.py`.

The functions stay pandas-only with no I/O (preserving the module's "pure,
dependency-free" property). Broaden the `staking.py` module docstring from "staking math"
to "staking math + its backtest summarization." See the PRD's first Implementation
Decision bullet.

Rewrite `backtest_staking.py` so it becomes a **thin CLI wrapper**: it keeps only argument
parsing, terminal formatting (`_fmt` / `_print_summary` / `analyse`), default-path
resolution (`_resolve_default_path`), and the prominent SP-placeholder `_CAVEAT` banner —
importing all staking math and summarization from `betting`. Its CLI behaviour and printed
output (including the loud banner) must be unchanged.

Relocate the staking-summary tests from `tests/scripts/test_backtest_staking.py` into the
`betting` test package (`tests/betting/`), importing the new **public** function names
instead of the private helpers. Preserve the existing fixtures and assertions so the move
proves behaviour is unchanged (this is the prior-art consolidation called out in the PRD's
Testing Decisions). Any genuinely CLI-level test (banner / `analyse`) stays under
`tests/scripts/`; if no CLI test remains, the old test file is removed rather than left
empty.

## Acceptance criteria

- [ ] `race_analytics/betting/staking.py` exposes `attach_stakes`, `identify_picks`, `summarise`, and `backtest` (final public names at implementer's discretion) as public pure functions; `betting/__init__.py` re-exports them in `__all__`
- [ ] `staking.py` module docstring broadened to cover backtest summarization; module remains import-only with no I/O
- [ ] `backtest_staking.py` imports the summary functions from `betting` and retains only CLI parsing, formatting, default-path resolution, and the `_CAVEAT` banner; no staking/summary math is defined locally
- [ ] `python -m race_analytics.scripts.backtest_staking <some evaluation_results_*.csv>` prints the same summary and SP-placeholder banner as before the refactor
- [ ] The staking-summary tests live under `tests/betting/` and import the new public names; their fixtures and assertions are unchanged
- [ ] `pytest tests/betting/` and `pytest tests/scripts/test_backtest_staking.py` (if it still exists) pass

## Blocked by

None - can start immediately.

## User stories addressed

Reference by number from the parent PRD:

- User story 11 (one canonical implementation in the `betting` package)
- User story 12 (`backtest_staking.py` keeps its SP-placeholder banner)
- User story 14 (moved functions covered by the same tests, relocated to the `betting` test package)
