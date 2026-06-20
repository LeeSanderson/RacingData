# Issue 004 — Docs

**Type:** AFK

## Parent PRD

`issues/prd.md` — see *Further Notes* (documentation updates and the backfill future-idea) and the Issue D entry in the Delivery / Issue Breakdown.

## What to build

Document the new pre-race columns and record the deferred backfill idea. This slice is written against the PRD's intended behaviour and does not require the code slices to have merged.

- **`docs/data-pitfalls.md`** — state clearly that the `Card*` ratings (`CardOfficialRating`/`CardRacingPostRating`/`CardTopSpeedRating`) are **pre-race and non-leaky** and may be used directly as features, while the inherited results ratings (`OfficialRating`/`RacingPostRating`/`TopSpeedRating`) remain **post-race and leaky**. Add the **forward-only coverage caveat**: these columns populate from deployment forward, so coverage starts at deployment date and historical rows are blank by design. Note the prize-money currency caveat (not normalised across countries).
- **`AGENTS.md`** — add a one-liner in the no-leakage constraints pointing to `Card*` as the pre-race-safe rating source (so a reader does not conclude "all ratings are banned" or feed a leaky column to a model).
- **`docs/odds-capture.md`** — extend to describe the generalised **one-mechanism, six-column** card→result write-back (the forecast-odds merge is now one field among several).
- **`issues/todo.md`** — add a future-idea entry, sibling to the existing "Backfill ForecastDecimalOdds into historic Results" item, noting that form figures / days-since-last-run / prize money are pre-race facts that may already appear on the daily-scraped result pages and could therefore be backfilled across history by a single re-scrape — unlike the ratings, which are post-race on result pages.

## Acceptance criteria

- [x] `docs/data-pitfalls.md` distinguishes `Card*` (pre-race, safe-to-use) from inherited results ratings (post-race, leaky), and documents the forward-only coverage caveat and the prize-money currency caveat.
- [x] `AGENTS.md` no-leakage constraints reference `Card*` as the pre-race-safe rating source.
- [x] `docs/odds-capture.md` describes the generalised one-mechanism, six-column write-back.
- [x] `issues/todo.md` has the backfill future-idea entry sibling to the ForecastDecimalOdds backfill item, scoped to the three non-rating fields and explaining why the ratings are excluded.

## Blocked by

None - can start immediately (independent; intended to be done last).

## User stories addressed

- User story 17 (`Card*` ratings documented as pre-race safe vs leaky inherited ratings)
- User story 18 (forward-only coverage documented)
- User story 19 (backfill recorded as a future idea)
