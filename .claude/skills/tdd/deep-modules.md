# Deep Modules

From "A Philosophy of Software Design":

**Deep module** = small interface + lots of implementation

```
┌─────────────────────┐
│   Small Interface   │  ← Few methods, simple params
├─────────────────────┤
│                     │
│                     │
│  Deep Implementation│  ← Complex logic hidden
│                     │
│                     │
└─────────────────────┘
```

**Shallow module** = large interface + little implementation (avoid)

```
┌─────────────────────────────────┐
│       Large Interface           │  ← Many methods, complex params
├─────────────────────────────────┤
│  Thin Implementation            │  ← Just passes through
└─────────────────────────────────┘
```

## Examples in this codebase

**Deep modules to imitate:**

- `RacingResultParser.Parse(string html) → Task<RaceResult>` — one entry point, hides all the `HtmlNodeFinder` selectors, runner parsing, status normalization, and length-per-second scaling.
- `RaceCardParser.Parse(string html) → Task<RaceCard>` — same shape.
- `IRacingDataDownloader` — four methods that hide the URL construction, HTML loading, retry handling, and node-finding for both results and racecards.
- `UpdateResultsCommandHandler.RunAsync(UpdateResultsOptions)` — one method that hides month-splitting, existing-file detection, partial backfill, and CSV serialization.

**Watch for shallow drift:**

- Per-field getters on a parser (`GetCourseName(html)`, `GetGoing(html)`, `GetRunners(html)`) — the interface becomes as wide as the data model; merge into a single `Parse`.
- Helper classes that exist only to be called by one caller and only forward to a single library call — fold them into the caller or deepen them with the surrounding logic.

When designing or reviewing an interface, ask:

- Can I reduce the number of methods?
- Can I simplify the parameters? (Prefer an options record like `UpdateResultsOptions` over six positional args.)
- Can I hide more complexity inside? (Could the caller stop knowing about `HtmlNodeFinder`, `RaceCardRunnerParser`, etc.?)
