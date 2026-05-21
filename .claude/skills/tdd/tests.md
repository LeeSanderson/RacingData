# Good and Bad Tests

This project's C# test suite uses **xUnit + FluentAssertions + NSubstitute + Verify** (snapshot testing). Tests are named `{Class}Should.{Behavior}` (e.g. `UpdateResultsCommandHandlerShould.BackFillDataForThe11ThWhenGetting2DaysOfDataAndTodayIs13ThAndHaveExistingDataFor12Th`). The Python side under `Data/` runs as notebooks/scripts and is mostly tested by running the full `run.ps1` pipeline.

## Good Tests

**Integration-style**: Drive a command handler through its public `RunAsync` entry point with mocked system boundaries (`IFileSystem`, `IClock`, `IRacingDataDownloader`), then assert on the observable side-effect — the CSV content captured by `MockFileSystemBuilder`.

```csharp
// GOOD: drives UpdateResultsCommandHandler through its public entry point
[Fact]
public async Task DownloadResultsWhenNoResultsExist()
{
    var result = await ExecuteHandler(minimumPeriodInDays: 1);

    result.Should().Be(ExitCodes.Success);
    await Verify(_mockFileSystemBuilder.GetContent(ResultsFileForMay2022));
}
```

Characteristics:

- Calls the real `UpdateResultsCommandHandler.RunAsync` — no internal types mocked
- Mocks only the system boundaries (`IClock`, `IFileSystem`, `IRacingDataDownloader`)
- Asserts on the CSV content actually written (via `Verify` snapshot), not on which collaborators were called
- Would survive a refactor that splits or merges private helpers like `UpdateMonthlyResultsFile`

For pure parsers (`RacingResultParser`, `RaceCardParser`, `RunnerParser`), feed real fixture HTML (`FakeData.BathRaceResultFor1730RaceOn20220511`) and assert on the parsed `RaceResult` / `RaceCard`. The parser is a deep module — drive it through `Parse`, not its private node-finding helpers.

For Python feature builders (`HorseStatsBuilder.py`, `JockeyStatsBuilder.py`), prefer tests that load a small fixture `Race_Features.csv`, run the script-as-function, and assert on the resulting DataFrame shape/values:

```python
# GOOD: exercises real pandas pipeline, asserts on output
def test_horse_stats_builder_carries_forward_avg_finishing_position():
    races = pd.read_csv("fixtures/race_features_small.csv")
    races["Off"] = pd.to_datetime(races["Off"])

    horse_stats = build_horse_stats(races)

    row = horse_stats.loc[horse_stats["HorseId"] == 12345].iloc[0]
    assert row["NumberOfPriorRaces"] == 3
    assert row["AvgRelFinishingPosition"] == pytest.approx(0.42, abs=0.01)
```

## Bad Tests

**Implementation-detail tests**: Coupled to internal collaborators or the way the handler is wired together.

```csharp
// BAD: asserts on which URLs the downloader was asked for
[Fact]
public async Task UpdateResults_CallsDownloaderForEachMonth()
{
    await ExecuteHandler(minimumPeriodInDays: 60);

    await _mockRacingDataDownloader.Received(2)
        .GetResultUrls(Arg.Any<DateOnly>(), Arg.Any<DateOnly>());
}
```

Red flags:

- Asserts on call counts/arguments of an internal collaborator (`Received(2)`, `DidNotReceive()` on something that *isn't* a true system boundary)
- Test name describes HOW (calls downloader twice) not WHAT (backfills missing days)
- Test breaks if `UpdateResultsCommandHandler` switches from per-month iteration to a single range call, even though the resulting CSV is identical

```csharp
// BAD: bypasses the handler to verify behavior
[Fact]
public async Task UpdateResults_ParsesRaceResultsCorrectly()
{
    var parser = new RacingResultParser();
    var result = await parser.Parse(FakeData.BathRaceResultFor1730RaceOn20220511);
    result.Runners.Should().HaveCount(8);
}
```

This is fine **as a parser test**, but not as an "UpdateResults" test — verify the handler's behavior through the file it produces, not by independently invoking the parser.

```python
# BAD: asserts on a private intermediate variable
def test_horse_stats_uses_groupby_first():
    races = load_fixture()
    grouped = races.groupby("HorseId").first()  # reaching inside the builder
    assert len(grouped) == 5
```

The test names a private step of the implementation. Test what `build_horse_stats` returns, not how it gets there.
