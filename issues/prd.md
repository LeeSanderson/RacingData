# PRD: Kelly-staked ROI in the evaluation metrics

## Problem Statement

When I run the walk-forward evaluator to choose between prediction algorithms, I see
three things per algorithm: accuracy, flat-£1 ROI, and the market-favourite baseline. I
do **not** see what each algorithm would have returned under the staking strategy the
production pipeline actually uses — fractional Kelly behind a value gate.

That Kelly figure does exist, but only in a *separate* diagnostic script
(`backtest_staking.py`) that has to be run as a second pass over a saved
`evaluation_results_*.csv`. So comparing algorithms on their staked return is a manual,
two-step chore, and the staked figure isn't sitting next to accuracy/flat-ROI where I
make the decision. I want the Kelly return and its coverage reported inline by the
evaluator itself, so a single run gives me every metric I need to rank algorithms.

I am aware that real morning forecast prices are not yet in the training/eval window
(capture began ~2026-06, history is almost entirely post-race SP), so today the Kelly
figure is a diagnostic measuring the staking *mechanics* against an SP placeholder, not
real forecast-time profitability. The point of building it now is that the metric becomes
meaningful automatically, with no further code change, once forecast coverage matures
(the ≥80% re-eval trigger, ~Jan 2027).

## Solution

Move the Kelly staking-summary logic out of the diagnostic script and into the `betting`
domain as reusable, pure functions, then call those functions from the evaluator so that
**Kelly net £** and **Kelly coverage %** are reported per algorithm everywhere flat ROI
is already reported: the per-fold line, the cross-fold Summary table, and the
Early-vs-Late stability split.

Because the evaluator already retains, for every (algorithm, fold), the exact full-field
frame it writes to the results CSV, the inline Kelly numbers are computed from the *same
data* the diagnostic script reads — so the inline figure is guaranteed identical to
running `backtest_staking.py` over the saved CSV. The diagnostic script remains, reduced
to a thin command-line wrapper (parsing, printing, and its loud SP-placeholder banner)
over the shared functions.

## User Stories

1. As an algorithm evaluator, I want Kelly net £ shown per algorithm in the cross-fold
   Summary table, so that I can compare staked return without running a second script.
2. As an algorithm evaluator, I want Kelly coverage % shown alongside Kelly net £, so that
   I can tell a strong return on a few value-gated bets apart from one earned across most
   races.
3. As an algorithm evaluator, I want the existing accuracy, flat-£1 ROI, favourite
   baseline, and timing metrics to remain exactly as they are, so that nothing I rely on
   today regresses.
4. As an algorithm evaluator, I want Kelly net £ and coverage % on the per-fold line, so
   that I can watch the staked return accumulate fold by fold.
5. As an algorithm evaluator, I want Kelly net £ and coverage % in the Early-vs-Late
   stability split, so that I can judge whether an algorithm's staked edge is stable over
   time, not just its flat ROI.
6. As an algorithm evaluator, I want the inline Kelly figure to equal what
   `backtest_staking.py` produces over the same saved results, so that I can trust the two
   numbers are the same calculation and never have to reconcile a discrepancy.
7. As an algorithm evaluator, I want the Kelly return computed with the same odds and
   net-P&L convention as the existing flat ROI (decimal odds; won → stake×(odds−1),
   lost → −stake), so that flat and Kelly differ only by stake size and the value gate,
   not by accounting.
8. As an algorithm evaluator, I want Kelly figures aggregated additively across folds
   (sum the returns, sum the bet and race counts, recompute coverage at the end) rather
   than by averaging per-fold ratios, so that the cross-fold numbers are statistically
   correct.
9. As an algorithm evaluator, I want algorithms that emit no win probability (the
   regression models) to show `n/a` / 0% for Kelly rather than a misleading zero or an
   error, so that the table is honest about which models can be value-staked.
10. As an algorithm evaluator, I want the Kelly columns to appear even when I do not pass
    `--save-results`, so that I get the metric on every run, not only when I persist the
    CSV.
11. As a maintainer, I want one canonical implementation of the staking summary in the
    `betting` package, so that the evaluator and the diagnostic script can never drift
    apart.
12. As a maintainer, I want `backtest_staking.py` to keep its prominent
    SP-placeholder / diagnostic-only banner, so that anyone reading its output still
    understands the honesty caveat after the refactor.
13. As a maintainer, I want the Kelly columns in the evaluator to carry **no** extra
    diagnostic label, so that the Summary stays compact; the caveat lives in the
    diagnostic script and the project docs.
14. As a maintainer, I want the moved staking-summary functions covered by the same tests
    that cover them today, relocated to the `betting` test package, so that the refactor
    preserves existing behaviour.
15. As a maintainer, I want a test asserting the evaluator's inline Kelly aggregation
    equals the shared backtest summary over the same frame, so that the parity guarantee
    is enforced and not just asserted in prose.
16. As a future maintainer, I want `docs/staking.md` and `evaluations.md` to record that
    Kelly £/coverage is now reported inline by the evaluator, so that the documentation
    matches the tool.
17. As an algorithm evaluator, I want algorithm *selection* to continue to rest on flat
    ROI plus early/late stability for now, with Kelly riding along as an informational
    signal, so that I do not accidentally promote on an SP-placeholder artefact before
    forecast coverage matures.

## Implementation Decisions

- **Shared staking-summary logic lives in the existing `betting/staking.py` module.** The
  four summary helpers currently private to the diagnostic script (attach stakes to a
  field, identify the rank-1 pick per race, summarise staked vs flat performance, run the
  per-algorithm backtest) are moved into `staking.py` as **public, pure** functions and
  re-exported from the `betting` package's public surface. They remain pandas-only with no
  I/O, preserving the module's "pure, dependency-free" property; the module docstring is
  broadened from "staking math" to "staking math + its backtest summarization."
- **`backtest_staking.py` becomes a thin CLI wrapper.** It keeps only argument parsing,
  terminal formatting, the default-path resolution, and the SP-placeholder banner; all
  staking math and summarization is imported from `betting`. Its CLI behaviour and output
  are unchanged.
- **The evaluator computes Kelly inline from the frames it already builds.** For every
  (algorithm, fold) it already constructs the full-field result frame that is written to
  the CSV (carrying win probability, market probability, resolved odds, finishing
  position). These frames are retained per algorithm so the same data feeds the Kelly
  summary — guaranteeing the inline figure equals the diagnostic script's figure by
  construction.
- **Metric definition (locked).** Kelly headline = **net £ P&L** using decimal odds:
  per placed bet, won → `stake × (odds − 1)`, lost → `− stake`; summed over placed bets.
  Coverage % = placed bets ÷ settleable races. This is the same convention as the existing
  flat ROI — flat and Kelly differ only by variable stake size and the value-gate
  abstention. The per-£1 ratio and full stake distribution remain available in the
  diagnostic script but are not added to the evaluator's tables.
- **Cross-fold aggregation is additive.** Returns and bet/race counts are summed across
  folds and ratios recomputed at the end (achieved by concatenating the retained per-fold
  frames and summarising once), never by averaging per-fold ratios.
- **Placement.** Kelly net £ and Kelly coverage % are added to (1) the per-fold line, (2)
  the cross-fold Summary table, and (3) the Early-vs-Late stability split. The per-fold
  print is reordered so the fold's staking frame is built before the line is printed. The
  existing `ROI` column header is left unchanged; two new columns `Kelly £` and `Kelly%`
  are appended. The ROI-vs-coverage frontier table is left untouched (it sweeps the
  confidence gate, a different mechanism from Kelly's value gate).
- **Non-probabilistic algorithms.** Algorithms without a win-probability output produce no
  staked bets and report `n/a` / 0% coverage for Kelly — the correct outcome, not an error.
- **Independence from `--save-results`.** The Kelly figures are computed on every run; they
  do not depend on persisting the results CSV.
- **No selection-policy change.** Promotion of `ACTIVE_ALGORITHM` continues to rest on flat
  ROI + early/late stability while history is SP-derived. The Kelly columns are
  informational until the documented ≥80% forecast-coverage re-eval trigger fires.
- **Documentation.** `docs/staking.md` and the methodology note in `evaluations.md` are
  updated to state that Kelly £/coverage is now reported inline by the evaluator.

## Testing Decisions

- **What makes a good test here:** exercise the public staking-summary functions and the
  evaluator's aggregation through their behaviour — feed an eval-results-shaped frame in,
  assert on the summary numbers out (bets, coverage, flat profit, Kelly profit) — rather
  than asserting on internal structure. This matches the existing staking tests.
- **Relocated tests.** The current staking-summary tests (today importing private helpers
  from the diagnostic script) move into the `betting` test package and import the new
  public function names. Their fixtures and assertions are preserved so the move proves
  behaviour is unchanged. Prior art: the existing `tests/betting/test_staking.py`
  (staking math) and `tests/scripts/test_backtest_staking.py` (summary helpers) being
  consolidated under `tests/betting/`.
- **New parity test.** A test asserts that the evaluator's inline Kelly aggregation over a
  set of per-fold frames produces the same summary as calling the shared backtest function
  over the concatenation of those frames — formalising the "inline == offline backtest"
  guarantee.
- **Edge cases to cover (already present for the helpers, retained):** a value bet sized
  and the rest zeroed; rank-1 pick selection carrying its stake; coverage as a valid
  fraction; the no-bets case not dividing by zero; an empty frame; legacy frames missing
  the staking columns staking nothing; decimal-odds fallback when resolved odds are absent;
  per-algorithm independence so stakes are normalised within one model's field.
- **Python test framework.** This PRD is entirely in the Python ML stage. Unlike the older
  `Data/*.py` scripts, the `race_analytics` package has real pytest coverage in `tests/`
  mirroring the package layout, so all of the above are pytest unit tests — no reliance on
  eyeballing `run.ps1` output.

## Out of Scope

- **Tuning any staking parameter.** `KELLY_FRACTION`, `MIN_EDGE`, `CAP`, and `BANKROLL`
  keep their current calibrated values; this PRD reports the return at those settings, it
  does not optimise them, and adds no parameter sweep.
- **Changing the algorithm-selection / promotion policy.** Selection stays flat ROI +
  early/late stability while history is SP-derived; Kelly does not become a promotion gate
  under this PRD.
- **Capturing or backfilling real forecast/live odds.** The forecast-coverage maturation
  and live-odds capture are the separate Phase-2 / re-eval items already tracked in
  `issues/todo.md`.
- **Adding the per-£1 Kelly ratio or the stake distribution to the evaluator's tables.**
  Those stay in the diagnostic script.
- **Any change to the C# extraction stage**, the CSV schema, or `run.ps1` — this is a
  Python-only, evaluation-time change.
- **Touching the ROI-vs-coverage frontier output.**

## Further Notes

- The honesty framing is deliberate: the Kelly columns carry no diagnostic label inside the
  evaluator (kept compact), while the diagnostic script retains its prominent banner and
  the docs carry the caveat. The same SP-placeholder reasoning documented for the existing
  MarketProb and staking diagnostics in `evaluations.md` applies to these inline numbers
  until the ≥80% forecast-coverage trigger fires.
- The strongest design property to preserve through implementation is the **single source
  of truth**: the evaluator and the diagnostic script must call the *same* summarization
  function over the *same* per-fold frames, so the two can never report different Kelly
  numbers for the same run.
