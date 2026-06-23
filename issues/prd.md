# PRD — Forward all pre-race card fields into results, and refactor the record hierarchy

> Two related changes under one PRD, sequenced as two issues (refactor first):
> **(1)** extract a shared base record so `RaceResultRecord` stops inheriting — and shadowing —
> `RaceCardRecord`'s pre-race columns; **(2)** fix the card→result write-back so that *every*
> pre-race fact captured on the morning card (owner, breeding, the nine per-runner extras) is
> forwarded onto the matching result row, exactly as forecast odds, `Card*` ratings, days-since,
> form and prize money already are.
>
> Guiding principle: **the monthly `Results_YYYYMM.csv` files are the training corpus for future
> predictions.** A pre-race fact captured on the card but never carried onto the result is invisible
> to the model — so capturing it was wasted effort.

## Problem Statement

The racecard extra-data capture PRD (now shipped) added owner, breeding (sire/dam) and nine
per-runner "extras" (first-time headgear/gelding/jockey flags, wind-surgery, trainer current form,
jockey allowance, new-trainer count, country of origin, Spotlight prose) as columns on the daily
`TodaysRaceCards.csv`. These are all static, leak-free pre-race facts.

But the `validate` step's card→result write-back — the mechanism that carries the morning card's
pre-race data onto results once a race has been run — was built (and last generalised) **before**
breeding and the extras were captured. It forwards only forecast odds, the `Card*` pre-race
ratings, days-since-last-run, form figures and prize money. **Owner, breeding and all nine extras
are captured each morning but never reach the result rows.** Because card capture has no archive,
and because the daily card file is overwritten every day, those values are effectively lost the
moment the day rolls over: they never enter the training corpus the Python eval pipeline reads.

This is a genuine forwarding bug, not a deliberate exclusion — the fields were simply added to
capture after the write-back was written, and nobody extended it.

Underlying the bug is a structural problem. `RaceResultRecord` inherits from `RaceCardRecord`, but
the two records only genuinely share their first block of columns (race + runner identity,
attributes and the pre-race stats). Everything `RaceCardRecord` adds beyond that block collides, by
CSV column index, with the result's own post-race columns. To avoid the collision, every new card
field has had to be re-declared on `RaceResultRecord` with `new` at an ever-higher index, each
wrapped in a paragraph of explanation. The inheritance buys no polymorphism (nothing ever treats a
result as a card), yet it forces those always-blank shadow columns onto the result and makes every
future card field a fragile, manual re-shadowing exercise. It also actively obscured the forwarding
bug, since the shadow columns *looked* present on the result.

## Solution

**Refactor first (behaviour-preserving), then fix the bug.**

1. **Extract a shared base record.** Introduce an abstract `RaceRunnerRecord` holding only the
   columns the card and result genuinely share (the race + runner identity/attributes/stats block,
   CSV indices 0–33). Make both `RaceCardRecord` and `RaceResultRecord` inherit from it as
   *siblings*. `RaceResultRecord` no longer inherits the card's pre-race extras, so all the `new`
   shadowing disappears and each record simply declares its own columns above index 33. Every
   existing CSV column index is frozen, so card and result files on disk round-trip byte-identically
   and the Python stage is unaffected. This change adds and removes no data — it is pure structure.

2. **Forward the missing pre-race fields.** Extend the `validate` card→result write-back so that
   owner (2 columns), breeding (3) and the nine extras are carried from the card onto the matching
   result row, using the same per-field presence + blank-fill, forward-only, idempotent rules the
   eight already-forwarded fields use. After this, every pre-race fact captured on the card reaches
   the result corpus from go-live onward.

The result: a clean two-sibling record hierarchy that no longer needs shadowing tricks, and a
results corpus that finally contains the full set of captured pre-race signals for model training.

## User Stories

1. As a modeller training on the monthly `Results_YYYYMM.csv` corpus, I want the owner of each
   runner carried onto the result row, so that I can build owner strike-rate features from history.
2. As a modeller, I want sire, sire-country and dam carried onto the result row, so that I can build
   pedigree/aptitude features for lightly-raced types whose form is thin.
3. As a modeller, I want the first-time headgear, gelding and jockey flags carried onto the result
   row, so that I can model the recognised first-time-equipment improvement angle.
4. As a modeller, I want wind-surgery, trainer current form (`TrainerRtf`), jockey allowance,
   new-trainer count and country of origin carried onto the result row, so that none of the captured
   pre-race signals is stranded on the card file.
5. As a modeller, I want the per-runner Spotlight prose carried onto the result row, so that the raw
   text corpus accrues against finished races for a future NLP pipeline.
6. As a modeller, I want a `bool?` first-time flag that was captured as `false` on the card to land
   as `false` (not null) on the result, so that I can distinguish "declared, did not fire" from
   "absent from the card" — the three-state signal is preserved end-to-end.
7. As a modeller, I want every forwarded field to be a pre-race fact only, so that nothing leaky
   (post-race ratings, finishing data) is introduced into the feature space by this change.
8. As the operator running the daily `validate` step, I want the forwarding to be idempotent, so
   that re-running on the same day never overwrites a cell that already holds a value.
9. As the operator, I want forwarding to be forward-only and gated on the card still being present,
   so that a result is filled only while that race's morning card is available and the step never
   invents data.
10. As the operator, I want a result cell filled only when the card actually carries the value, so
    that a runner left at a default (e.g. an "SP" forecast) or a genuinely-absent field never
    overwrites a result with empty data.
11. As the operator, I want the write-back to rewrite a results file only when at least one cell
    actually changed, so that no-op days don't churn the file.
12. As the operator, I want the `validate` step to keep working unchanged when the card file is
    missing, so that a day without a captured card still scores cleanly.
13. As a developer maintaining the record models, I want `RaceResultRecord` to stop inheriting
    `RaceCardRecord`, so that adding a future card column never again forces a `new`-shadowed
    re-declaration at a hand-picked index.
14. As a developer, I want the columns the card and result genuinely share to live in one shared
    base record, so that there is a single place to evolve the common block.
15. As a developer, I want the shared base to be abstract, so that the intent ("base only, never
    instantiated directly") is documented and enforced.
16. As a developer, I want the two `ListFrom` factories to stay independent rather than be merged
    behind a forced abstraction, so that the mapping code stays readable and no artificial interface
    is introduced into the domain layer just to serve CSV mapping.
17. As a data engineer with existing `TodaysRaceCards.csv` and `Results_YYYYMM.csv` files on disk, I
    want every CSV column index frozen across the refactor, so that historical files round-trip
    byte-identically and the Python eval stage needs no change.
18. As a data engineer, I want legacy files written before any of these columns existed to keep
    loading, so that the `[Optional]`/missing-field tolerance already in place continues to hold.
19. As a developer reviewing the change, I want the refactor to be provably behaviour-preserving via
    the existing test suite staying green, so that the structural change and the behavioural bug fix
    stay cleanly separated across the two issues.
20. As a developer, I want a characterization test that round-trips the full result layout including
    the previously-untested owner/breeding/extras columns, so that the refactor is caught if it
    perturbs any column.
21. As a maintainer reading the code, I want the now-obsolete comments about `new` shadowing and
    "stays blank in the results layout" removed or corrected, so that the comments describe the code
    as it actually behaves after the change.
22. As the pipeline owner, I want it understood that pre-capture historic result rows stay blank for
    these fields (no backfill), so that expectations about the usable modelling window are realistic
    and consistent with the earlier decision to drop owner historic-backfill.
23. As a punter consuming `TodaysPredictions.csv` downstream, I want the model eventually to learn
    from owner/breeding/extras once enough forward history accrues, so that predictions can improve
    from signals that are currently captured but discarded.

## Implementation Decisions

- **Two issues under one PRD, refactor first.** Issue 1 is the behaviour-preserving record refactor;
  Issue 2 is the forwarding bug fix and is *blocked-by* Issue 1, so the bug fix lands on the
  already-clean structure rather than on shadowed declarations.

- **Shared base record.** Introduce an abstract `RaceRunnerRecord` in the downloader's models layer,
  holding the 34 columns common to both records at CSV indices 0–33 (race identity, classification,
  distance, going/surface, runner identity, runner attributes, and the pre-race stats block
  including forecast odds and the pre-race OR/RPR/TSR). `RaceCardRecord` and `RaceResultRecord` both
  inherit from it.

- **Sibling records, no shadowing.** With the common block in the base, `RaceResultRecord` no longer
  inherits the card's pre-race extras, so the `new` keyword is dropped from every previously-shadowed
  property; each record declares only the columns it owns above index 33.

- **Frozen layout.** Every existing `[Index]` value is preserved exactly. The card layout is
  unchanged; the result layout keeps its current column order and indices (post-race columns,
  forecast odds, `Card*` ratings, then the forwarded card fields at their existing high indices).
  No on-disk format change; the Python stage is untouched.

- **Factories stay independent.** The two `ListFrom` methods are kept as separate per-type mappings.
  The card and result domain runner types share no common base/interface, so de-duplicating the
  common-field assignment would require either a new domain interface or a param-heavy helper — both
  judged worse than the shallow duplication they would remove. The base record's value is in the
  shared *property declarations*, not the factory bodies.

- **Forwarding set.** The `validate` card→result write-back is extended to carry, in addition to the
  eight fields it already forwards, these 14: `OwnerId`, `OwnerName`, `SireName`, `SireCountry`,
  `DamName`, `HeadgearFirstTime`, `GeldingFirstTime`, `WindSurgery`, `TrainerRtf`,
  `JockeyAllowanceLbs`, `JockeyFirstTime`, `NewTrainerRacesCount`, `CountryOfOrigin`, `Spotlight`.

- **Gating convention.** Each copy follows the established per-field presence + blank-fill rule, by
  type. Nullable value types are gated on "card has a value AND result cell is still null". Strings
  are gated on "card value is non-empty AND result cell is still empty" (matching form/prize). The
  three `bool?` flags are gated on presence (non-null), **never on truthiness**, so a card `false`
  is carried as `false` and stays distinct from null. The write-back remains forward-only and
  idempotent, and rewrites a results file only when at least one cell changed.

- **No new CLI verb or schema column.** All forwarded columns already exist on the result layout;
  this PRD only changes *which* of them the write-back fills. `run.ps1` wiring is unchanged — the
  `validate` step already runs the write-back before the card file is overwritten.

- **Naming distinction preserved.** Owner/breeding/extras forward name-to-name (they have no
  post-race counterpart on the result). This is unlike the pre-race ratings, which forward into the
  distinct `Card*` columns to stay separate from the post-race (leaky) OR/RPR/TSR — that existing
  behaviour is unchanged.

- **Documentation.** Obsolete structural comments (the `new`-shadowing / "re-declared at higher
  indices" explanations) are removed with the refactor. The "captured forward-only … not part of the
  write-back, so these stay blank in the results layout" comments are rewritten to state the fields
  are now forwarded. A targeted sweep of `issues/todo.md`, `docs/racecard-extra-data-audit.md` and
  `docs/data-pitfalls.md` corrects only lines that claim these stay blank in results; the separate
  historic-backfill item is left intact.

## Testing Decisions

- **Test external behaviour, not implementation.** As with the existing suite, drive the `validate`
  command handler via its public run entry point against a stateful in-memory file system and assert
  on the CSV that comes back out; assert record round-trips by serialising and re-reading. Do not
  test private methods directly.

- **Issue 1 (refactor) is guarded by the existing suite staying green and untouched.** The current
  card and result round-trip tests, and the full `validate` merge suite, are the regression net
  proving the structural change altered no behaviour. In addition, add one characterization test
  (written first, against current code, so it passes before the refactor) that round-trips the
  **full** result layout including the owner/breeding/extras columns at their high indices — the
  columns the refactor re-declares and which nothing currently round-trips — so any drift is caught.

- **Issue 2 (forwarding) is built test-first (red→green).** Add merge tests asserting: (a) all 14
  fields forward from a card runner onto a blank result row; (b) a `bool?` flag captured as `false`
  on the card lands as `false` on the result, not null; (c) per-field idempotency and blank-fill for
  a representative new field (an already-populated cell is kept; a still-blank cell is filled). Reuse
  and extend the existing card/result builder helpers with the new fields rather than hand-rolling
  records.

- **Prior art.** `ValidateRaceCardPredictionsCommandHandlerShould` (the existing forecast-odds and
  six-column write-back tests, including idempotency and the `Card*`-vs-post-race leakage guard) and
  the `RaceCardRecord`/`RaceResultRecord` round-trip and legacy-tolerance tests.

- **No Python tests.** This PRD touches no `Data/*.py`. The frozen-layout decision means the Python
  stage neither changes nor needs new coverage; the forwarded columns simply begin arriving
  populated on forward results.

## Out of Scope

- **Historic backfill.** No pre-capture result rows are filled. Forwarding is forward-only; rows
  whose morning card no longer exists stay blank for these fields (as the eight already-forwarded
  fields already do). This is consistent with the earlier decision to drop owner historic-backfill.
- **CSV index renumbering.** The result layout is not tidied; indices are frozen to keep the on-disk
  corpus stable.
- **Merging the `ListFrom` factories** behind a shared helper or a new domain interface.
- **Any Python / feature-engineering / eval change.** No `Race_Features.csv` columns, no model
  changes; this PRD only ensures the captured signals reach the results corpus.
- **NLP over Spotlight.** The prose is forwarded verbatim; no parsing or feature derivation here.
- **New pre-race fields.** Only the already-captured fields are forwarded; no new card capture.

## Further Notes

- **Leakage safety.** All 14 forwarded fields are static pre-race facts (identity, pedigree,
  declaration flags, a capture-time trainer-form snapshot). None is post-race, so forwarding them
  introduces no leakage into the training corpus.
- **Why the bug existed.** The write-back was generalised from the forecast-odds merge into a
  multi-column card→result write-back during the owner-capture issue, but it covered only forecast
  odds, the `Card*` ratings, days-since, form and prize money. Breeding and the extras were captured
  in later issues and the write-back was never extended; owner was captured in the same issue but
  not wired into its own write-back.
- **The refactor unblocks future capture.** Once the records are siblings, any future pre-race card
  column is a plain declaration plus one forwarding line — no shadowing, no hand-picked index, no
  always-blank shadow column on the result.
