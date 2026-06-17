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
time*. The Python predictor ignores card odds today, and it must stay that way —
the forecast must not silently become a model feature or selection/filter unless
deliberately and safely introduced. Full reasoning in `docs/data-pitfalls.md`.

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
