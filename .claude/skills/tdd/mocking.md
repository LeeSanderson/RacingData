# When to Mock

Mock at **system boundaries** only. In this codebase those boundaries are:

- **racingpost.com** — the only true external dependency. Hidden behind `IHtmlLoader` (production: `PuppeteerHtmlLoader` / `HttpClientHtmlLoader`) and surfaced one level up as `IRacingDataDownloader`.
- **The file system** — hidden behind `IFileSystem` from `System.IO.Abstractions`. All CSV/JSON I/O for monthly `Results_YYYYMM.csv` files goes through it.
- **The clock** — hidden behind `IClock` (`Today`, `IsToday`, `IsTomorrow`). Production uses `RealClock`; tests use `Substitute.For<IClock>()`.

**Don't mock:**

- Internal parsers (`RacingResultParser`, `RaceCardParser`, `RaceCardRunnerParser`, `RunnerParser`) — they're pure functions over HTML strings, exercise them with real fixture HTML from `FakeData`.
- `HtmlNodeFinder`, `LengthsPerSecondScaleTable`, `RaceResultRunner`, `RaceEntity` and other domain types — they're internal collaborators, not boundaries.
- Logging — pass `OutputLogger<T>` (test helper that forwards to `ITestOutputHelper`) instead of mocking `ILogger<T>`.

## Designing for Mockability

### 1. Constructor inject the boundary, never `new` it inside

The command handlers in `RaceDataDownloader/Commands/` all follow this pattern, which is what makes them testable end-to-end:

```csharp
// GOOD: every boundary is injected
public class UpdateResultsCommandHandler(
    IFileSystem fileSystem,
    IRacingDataDownloader downloader,
    IClock clock,
    ILogger<UpdateResultsCommandHandler> logger)
    : FileCommandHandlerBase<UpdateResultsCommandHandler, UpdateResultsOptions>(fileSystem, logger)
{
    protected override async Task InternalRunAsync(UpdateResultsOptions options) { ... }
}

// BAD: a handler that owns its dependencies — impossible to test without hitting the network
public class UpdateResultsCommandHandler
{
    private readonly HttpClient _http = new();
    private readonly IFileSystem _fs = new FileSystem();
    private DateOnly Today => DateOnly.FromDateTime(DateTime.Today);
}
```

### 2. Keep the boundary interface narrow and per-operation (SDK-style)

`IRacingDataDownloader` deliberately has one method per logical operation, so each can be stubbed independently:

```csharp
// GOOD: each operation is independently mockable
public interface IRacingDataDownloader
{
    IAsyncEnumerable<string> GetResultUrls(DateOnly start, DateOnly end);
    Task<RaceResult> DownloadResults(string url);
    IAsyncEnumerable<string> GetRaceCardUrls(DateOnly start, DateOnly end);
    Task<RaceCard> DownloadRaceCard(string url);
}

// BAD: one generic fetcher forces tests to branch on the URL inside the mock setup
public interface IRacingDataDownloader
{
    Task<object> Fetch(string kind, DateOnly date, string? url = null);
}
```

The narrow-per-operation style is what lets `MockRacingDataDownloader` compose stubs cleanly:

```csharp
_mockRacingDataDownloader = await MockRacingDataDownloader
    .New()
    .MockRaceResultUrls()
    .MockReturnBathRaceResults();
```

### 3. Stub returns, don't verify calls

NSubstitute makes both `.Returns(...)` and `.Received(n)` easy. Prefer `.Returns(...)` for boundary inputs and assert on the observable output (the CSV file content captured by `MockFileSystemBuilder._content`):

```csharp
// GOOD: arrange boundary behavior, assert on the file produced
_mockFileSystemBuilder.FileSystem.File.Exists(ResultsFileForMay2022).Returns(true);
await AddFakeResultsFile(ResultsFileForMay2022, 2022, 05, 11, 11);

var result = await ExecuteHandler(1);

result.Should().Be(ExitCodes.Success);
await _mockFileSystemBuilder.FileSystem.File
    .DidNotReceive().WriteAllTextAsync(ResultsFileForMay2022, Arg.Any<string>());
```

The `DidNotReceive` here is acceptable because *not writing the file* is the user-observable behavior we care about ("skip download when results already exist"). Contrast with asserting `.Received()` on `_mockRacingDataDownloader.GetResultUrls(...)` to verify internal sequencing — that's coupling to implementation.

### 4. For HTTP-layer tests, use `MockHttpMessageHandler`

The lower-level loaders (`HttpClientHtmlLoader`) take an `HttpClient`. Tests inject an `HttpClient` built from `RichardSzalay.MockHttp.MockHttpMessageHandler` to verify request shaping, retry, and error handling without mocking `HttpClient` itself.

## Python boundaries

The Python notebooks read/write CSV files directly via `pandas.read_csv` / `to_csv`. Treat the file system as the boundary: pass a path/`DataFrame` into a function under test rather than relying on the global working directory.

```python
# GOOD: function takes the DataFrame, returns the DataFrame
def build_horse_stats(races: pd.DataFrame) -> pd.DataFrame: ...

# BAD: function reads its input via a hard-coded path
def build_horse_stats() -> pd.DataFrame:
    races = pd.read_csv("Race_Features.csv")  # un-mockable in a test
    ...
```
