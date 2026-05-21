# Interface Design for Testability

Good interfaces make testing natural. The patterns the C# side of this codebase already follows:

## 1. Accept dependencies, don't create them

Command handlers receive every boundary by constructor, which is what makes `UpdateResultsCommandHandlerShould`, `DownloadResultsCommandHandlerShould`, etc. possible without hitting the network or the disk.

```csharp
// Testable — the test wires up substitutes for every boundary
public class UpdateResultsCommandHandler(
    IFileSystem fileSystem,
    IRacingDataDownloader downloader,
    IClock clock,
    ILogger<UpdateResultsCommandHandler> logger)
    : FileCommandHandlerBase<UpdateResultsCommandHandler, UpdateResultsOptions>(fileSystem, logger);

// Hard to test — the handler reaches for ambient state at runtime
public class UpdateResultsCommandHandler
{
    private readonly RacingDataDownloader _downloader =
        new(new PuppeteerHtmlLoader(), new RealClock());
    private DateOnly Today => DateOnly.FromDateTime(DateTime.Today);
}
```

The same applies to the Python side. A function that takes a `DataFrame` in and returns a `DataFrame` out is trivially testable; one that reads `Race_Features.csv` from the current directory is not.

```python
# Testable
def build_jockey_stats(races: pd.DataFrame) -> pd.DataFrame: ...

# Hard to test
def build_jockey_stats():
    races = pd.read_csv("Race_Features.csv")
    ...
    races.to_csv("Jockey_Stats.csv", index=False)
```

## 2. Return results, don't produce side effects

Prefer functions that compute and return over functions that mutate shared state. Parsers in `RacePredictor.Core.RacingPost` (`RacingResultParser.Parse`, `RaceCardParser.Parse`) take HTML in and return a `RaceResult` / `RaceCard` — no I/O, no statics, fully deterministic.

```csharp
// Testable
public Task<RaceResult> Parse(string html);

// Hard to test
public Task Parse(string html) // writes parsed records into a static cache
```

In Python, build new DataFrames with derived columns rather than mutating shared globals:

```python
# Testable — returns a new frame
def compute_avg_rel_finishing_position(horse_races: pd.DataFrame) -> pd.DataFrame:
    out = horse_races.copy()
    out["AvgRelFinishingPosition"] = (
        out["LastRaceAvgRelFinishingPosition"] * out["NumberOfPriorRaces"]
        + out["FinishingPosition"] / out["HorseCount"]
    ) / (out["NumberOfPriorRaces"] + 1)
    return out

# Hard to test — silently mutates a module-level frame
def compute_avg_rel_finishing_position():
    horse_races["AvgRelFinishingPosition"] = ...
```

## 3. Small surface area

`IRacingDataDownloader` exposes four methods — just enough to cover the result/racecard URL listing + download flows. `IClock` exposes three. `IHtmlLoader` exposes one. Each can be stubbed in a few lines of NSubstitute.

When designing a new module:

- Fewer methods → fewer tests needed
- Fewer parameters → simpler test setup (note how `RunAsync(TOptions options)` collapses a wide parameter list into a single options record)
- Hide complexity behind the method — the `UpdateMonthlyResultsFile` backfill logic is private, so tests only need to drive `RunAsync`
