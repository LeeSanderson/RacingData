# Odds Capture — Status & Roadmap

How runner prices are captured into the pipeline, what ships today, and what a
future implementer needs to know to add live market odds. For the *leakage* rule
that governs how these prices may (and may not) be used, see
[`docs/data-pitfalls.md`](data-pitfalls.md) — Pitfall 2.

There are two distinct prices, captured at different times:

| Price | When it exists | Where it lands |
| --- | --- | --- |
| **Forecast** (RP morning "tissue") | server-rendered when the card is published | card `FractionalOdds`/`DecimalOdds`; results `Forecast*` columns |
| **Live / market** | forms through the morning, closer to the off | **not captured yet** (Phase 2) |
| **SP** (post-race starting price) | after the race | results `FractionalOdds`/`DecimalOdds` |

## Phase 1 — forecast odds (shipped)

Each day's card now carries a **real pre-race price** for every runner instead of
the old `"SP"` placeholder:

- `RaceCardRunnerParser` reads the server-rendered `Section__BettingForecast` /
  `Link__BettingForecastHorse` block and assigns each runner its forecast price,
  keyed by the horse id in the anchor href. A runner with no forecast falls back
  to the `"SP"`/empty default. A non-empty card that yields **zero** forecasts
  logs a warning (soft canary for an RP markup change) but does not hard-fail.
- `Results_YYYYMM.csv` gained two trailing, **optional** columns —
  `ForecastFractionalOdds` (index 40) and `ForecastDecimalOdds` (index 41). The
  pre-existing `FractionalOdds`/`DecimalOdds` keep meaning the post-race **SP**.
- `validate` merges yesterday's forecast (still on `TodaysRaceCards.csv` at that
  point in `run.ps1`) into yesterday's just-refreshed results, matched on
  `(RaceId, HorseId)`. The merge is idempotent and forward-only (no backfill).
- The scheduled run moved to **09:00** (`.azuredevops/scheduled-run.yml`) to
  settle the schedule ahead of Phase 2; `run.ps1` step order is unchanged.

**Leakage guardrail:** a forecast price now exists on the card *at prediction
time*, and the predictor no longer ignores it — the market-prob work introduced
`MarketProb` (forecast-when-present-else-SP, per-race normalized) as a deliberately
sanctioned model feature, fed through a single resolver and evaluated honestly. The
SP fallback is transitional: with near-zero forecast coverage in history `MarketProb`
is mostly SP-derived today, and the fallback retires itself as forecast coverage
accrues. Raw card / SP / forecast prices remain barred as direct features, and no
odds-presence selection gate was added. A fully forecast-fed 7-month training window
is ~7 months away (a ~1-month checkpoint is still roughly six-sevenths SP), so the
re-eval that reconsiders adoption is gated on a coverage threshold, not a hard date.
Full reasoning in `docs/data-pitfalls.md` (Pitfall 2).

### The forecast merge is now one path among six fields

The `validate` write-back is **no longer forecast-specific**. It has been generalised
into a single **card→result data merge** — one read of `TodaysRaceCards.csv`, one
write per results file — that copies the forecast odds *plus* six new pre-race fields
from each card runner into the matching `(RaceId, HorseId)` result row:

| Card source | Result target |
| --- | --- |
| forecast `FractionalOdds` / `DecimalOdds` | `ForecastFractionalOdds` / `ForecastDecimalOdds` |
| pre-race `OfficialRating` | `CardOfficialRating` |
| pre-race `RacingPostRating` | `CardRacingPostRating` |
| pre-race `TopSpeedRating` | `CardTopSpeedRating` |
| `DaysSinceLastRun` | `DaysSinceLastRun` |
| `FormFigures` | `FormFigures` |
| `PrizeMoney` / `PrizeMoneyValue` | `PrizeMoney` / `PrizeMoneyValue` |

The character of the mechanism is unchanged from the forecast precedent: keyed on
`(RaceId, HorseId)`, **forward-only** (no backfill), and **per-field idempotent** —
each column is copied only when the card value is present *and* the result cell is
still blank, and a results file is rewritten only when at least one cell was filled.
The forecast odds are now simply one field on this one well-understood path, and their
original two-column blank rule is preserved exactly. Why the `Card*` ratings are
*pre-race and safe* (and the inherited result-page ratings are not) lives in
[`docs/data-pitfalls.md`](data-pitfalls.md) — Pitfall 1.

## Phase 2 — live / market odds (deferred)

Capturing the live bookmaker market (the Diffusion-fed "betting-odds" tab) is
deferred. It is the genuinely hard source: unavailable early, appearing only as
the market forms through the morning.

**Known blocker — the loader does not wait for the live feed.**
`PuppeteerHtmlLoader.GetHtmlResponseFrom` navigates with `page.GoToAsync(url)`
(which resolves on the `Load` event) and *immediately* calls
`page.GetContentAsync()`. The live-odds feed populates the DOM via a post-load
JS/Diffusion stream, so it is not present in the HTML captured at the load event.
Today's loader would return an empty/placeholder market.

**Phase 2 therefore needs:**
- A **wait strategy** so the live feed is in the DOM before content is read —
  e.g. `WaitForSelectorAsync` on a populated price element, tab activation if the
  odds tab must be clicked, or reading the odds endpoint/stream directly rather
  than scraping the rendered tab.
- An **empirical check of *when* prices populate** during the morning, to confirm
  the 09:00 run is early enough (or to choose a later capture) — the forecast is
  present at publish, but the live market may not be meaningful at 09:00.
- New **`Starting*` columns** on both the card and the results, parallel to the
  `Forecast*` columns, to store the live morning price distinct from forecast and
  SP. (Naming note: the user's "starting odds" = the *morning* live price, the
  inverse of the literal racing meaning of "Starting Price"; `Starting*` is used
  to stay explicit alongside `Forecast*`.)

A durable per-day card-odds archive was considered and rejected in favour of the
ephemeral same-run merge; revisit only if late-settling results prove a real loss.
