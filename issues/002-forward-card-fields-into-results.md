# Forward owner/breeding/extras onto result rows in the `validate` write-back

## Parent PRD

`issues/prd.md`

## What to build

Fix the genuine forwarding bug described in the PRD's *Problem Statement* and *Solution*
step 2: extend the `validate` step's card→result write-back so that **every** pre-race fact
captured on the morning card reaches the matching result row, not just the eight fields it
forwards today.

In `RaceDataDownloader/Commands/ValidateRaceCardPredictions/ValidateRaceCardPredictionsCommandHandler.cs`,
extend `MergeCardRunnerIntoResult` to also carry these **14** fields from the card runner onto
the matching `(RaceId, HorseId)` result row (see the PRD's *Forwarding set* decision):

`OwnerId`, `OwnerName`, `SireName`, `SireCountry`, `DamName`, `HeadgearFirstTime`,
`GeldingFirstTime`, `WindSurgery`, `TrainerRtf`, `JockeyAllowanceLbs`, `JockeyFirstTime`,
`NewTrainerRacesCount`, `CountryOfOrigin`, `Spotlight`.

Follow the established gating convention exactly (PRD *Gating convention*), by type:

- **Nullable value types** (`OwnerId`, `WindSurgery`, `TrainerRtf`, `JockeyAllowanceLbs`,
  `NewTrainerRacesCount`): fill only when the card has a value **AND** the result cell is still
  null.
- **Strings** (`OwnerName`, `SireName`, `SireCountry`, `DamName`, `CountryOfOrigin`,
  `Spotlight`): fill only when the card value is non-empty **AND** the result cell is still
  empty (matching the form/prize rule).
- **The three `bool?` flags** (`HeadgearFirstTime`, `GeldingFirstTime`, `JockeyFirstTime`):
  gate on presence (non-null), **never on truthiness**, so a card `false` is carried as
  `false` and stays distinct from null.

The write-back stays forward-only, idempotent, gated on the card file still being present, and
rewrites a results file only when at least one cell actually changed (the existing
`cellsFilled` accounting already provides this — the new copies must increment it).

These fields forward **name-to-name** (they have no post-race counterpart), unlike the pre-race
ratings which forward into the distinct `Card*` columns — that existing behaviour is unchanged.
No new CLI verb, no new schema column, no `run.ps1` change: all forwarded columns already exist
on the result layout; this only changes *which* of them the write-back fills.

Built **test-first (red → green)**: add merge tests before the handler change.

Documentation: correct the now-wrong `RaceResultRecord` comments that say these fields "stay
blank in the results layout" so they state the fields are now forwarded, and do a targeted
sweep of `issues/todo.md`, `docs/racecard-extra-data-audit.md` and `docs/data-pitfalls.md`,
correcting only lines that claim these stay blank in results. Leave the separate
historic-backfill item intact (no backfill is in scope).

## Acceptance criteria

- [ ] After the `validate` step runs against a present card and an existing results file, all
      14 fields forward from a card runner onto a blank matching result row (a new merge test
      asserts this on the round-tripped result CSV).
- [ ] A `bool?` flag captured as `false` on the card lands as `false` (not null) on the result
      row (dedicated test for the three-state distinction).
- [ ] Per-field idempotency + blank-fill holds for a representative new field: an
      already-populated result cell is kept (not overwritten) and a still-blank cell is filled
      (test asserts both on a re-run).
- [ ] A runner left at a default/absent value on the card (e.g. genuinely-null owner) does
      **not** overwrite the corresponding result cell with empty data.
- [ ] The write-back still rewrites a results file only when at least one cell changed
      (no-op days do not churn the file) and still skips cleanly when the card file is missing —
      existing tests for these stay green.
- [ ] All 14 forwarded fields are pre-race facts only; no post-race / finishing column is
      touched (the `Card*`-vs-post-race leakage guard test stays green).
- [ ] The "stays blank in the results layout" comments on `RaceResultRecord` are rewritten to
      say the fields are now forwarded; `issues/todo.md`, `docs/racecard-extra-data-audit.md`
      and `docs/data-pitfalls.md` lines claiming these stay blank in results are corrected; the
      historic-backfill item is left intact.
- [ ] Tests reuse/extend the existing card/result builder helpers with the new fields rather
      than hand-rolling records; `dotnet build` and the full suite pass.

## Blocked by

- Blocked by `issues/001-extract-shared-race-runner-record-base.md` (the forwarding fix lands
  on the clean two-sibling structure, not on shadowed declarations).

## User stories addressed

Reference by number from the parent PRD:

- User story 1 (owner forwarded)
- User story 2 (sire / sire-country / dam forwarded)
- User story 3 (first-time headgear/gelding/jockey flags forwarded)
- User story 4 (wind-surgery, `TrainerRtf`, jockey allowance, new-trainer count, country of origin forwarded)
- User story 5 (Spotlight prose forwarded)
- User story 6 (`bool?` `false` lands as `false`, not null)
- User story 7 (every forwarded field is pre-race / leak-free)
- User story 8 (forwarding is idempotent)
- User story 9 (forward-only, gated on the card still being present)
- User story 10 (a cell is filled only when the card actually carries the value)
- User story 11 (results file rewritten only when at least one cell changed)
- User story 12 (`validate` keeps working when the card file is missing)
- User story 21 (the "stays blank in results" comments corrected — structural-comment half is in `issues/001`)
- User story 22 (pre-capture historic rows stay blank; no backfill)
- User story 23 (model can eventually learn from owner/breeding/extras once forward history accrues)
