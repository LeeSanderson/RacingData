# Extract shared `RaceRunnerRecord` base (behaviour-preserving refactor)

## Parent PRD

`issues/prd.md`

## What to build

A pure structural refactor of the downloader's record models that adds and removes **no**
data — see the PRD's *Solution* step 1 and the *Shared base record* / *Sibling records* /
*Frozen layout* / *Factories stay independent* implementation decisions.

Introduce an **abstract** `RaceRunnerRecord` in `RaceDataDownloader/Models/` holding only the
34 columns the card and result genuinely share (CSV indices 0–33: race identity,
classification, distance, going/surface, runner identity, runner attributes, and the pre-race
stats block including forecast odds and the pre-race OR/RPR/TSR). Make both `RaceCardRecord`
and `RaceResultRecord` inherit from it as **siblings**.

With the common block in the base, `RaceResultRecord` no longer inherits the card's pre-race
extras, so the `new` keyword is dropped from every previously-shadowed property — each record
declares only the columns it owns above index 33. **Every existing `[Index]` value is frozen
exactly**, so on-disk card and result files round-trip byte-identically and the Python stage
is untouched.

Keep the two `ListFrom` factory methods independent (no shared helper, no new domain
interface) — the base record's value is in the shared *property declarations*, not the factory
bodies.

Remove the now-obsolete structural comments that explain the `new`-shadowing / "re-declared at
higher indices" mechanism (e.g. lines around `RaceResultRecord` indices 42–62), since that
mechanism no longer exists after the refactor. Do **not** touch the "captured forward-only …
stays blank in the results layout" claims yet — those are corrected in `issues/002` when the
fields actually begin forwarding.

This issue is the structural half only; the forwarding bug fix is `issues/002`, which lands on
the already-clean structure.

## Acceptance criteria

- [ ] An abstract `RaceRunnerRecord` exists in `RaceDataDownloader/Models/` declaring the
      shared columns at CSV indices 0–33; `RaceCardRecord` and `RaceResultRecord` both inherit
      from it and neither declares a `new`-shadowed property.
- [ ] Every `[Index]` value across the card and result layouts is unchanged from before the
      refactor (card 0–51, result 0–62), verified by the round-trip tests still asserting the
      same column order/positions.
- [ ] A characterization test is added **first** (committed/written against the current code so
      it passes before the refactor) that round-trips the **full** `RaceResultRecord` layout —
      including the owner/breeding/extras columns at indices 49–62 that nothing currently
      round-trips — and still passes after the refactor.
- [ ] The existing `RaceCardRecordShould`, `RaceResultRecordShould` and
      `ValidateRaceCardPredictionsCommandHandlerShould` suites stay green and unmodified
      (except where a test references the moved property declarations), proving behaviour is
      preserved.
- [ ] Legacy CSV files written before these columns existed still load (the existing
      `[Optional]` / missing-field tolerance continues to hold).
- [ ] The obsolete `new`-shadowing / "re-declared at higher indices" comments are removed; the
      "stays blank in results" comments are left untouched for `issues/002`.
- [ ] `dotnet build` and the full test suite pass; no behavioural diff (this is the
      separation point between structure and the bug fix).

## Blocked by

None - can start immediately.

## User stories addressed

Reference by number from the parent PRD:

- User story 13 (`RaceResultRecord` stops inheriting `RaceCardRecord`)
- User story 14 (shared columns live in one base record)
- User story 15 (base is abstract)
- User story 16 (the two `ListFrom` factories stay independent)
- User story 17 (every CSV index frozen; files round-trip byte-identically)
- User story 18 (legacy files keep loading)
- User story 19 (refactor provably behaviour-preserving via the green suite)
- User story 20 (characterization test round-trips the full result layout)
- User story 21 (obsolete `new`-shadowing comments removed — comment-correction half is in `issues/002`)
