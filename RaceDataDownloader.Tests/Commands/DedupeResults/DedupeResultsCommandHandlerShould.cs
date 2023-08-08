using System.IO.Abstractions;
using AutoFixture;
using NSubstitute;
using RaceDataDownloader.Commands;
using RaceDataDownloader.Commands.DedupeResults;
using RaceDataDownloader.Models;
using Xunit.Abstractions;

namespace RaceDataDownloader.Tests.Commands.DedupeResults;

public class DedupeResultsCommandHandlerShould
{
    private const string MockDataDirectory = @"c:\out";
    private const string ResultsFileForMay2022 = @"c:\out\Results_202205.csv";

    private readonly OutputLogger<DedupeResultsCommandHandler> _logger;
    private readonly IFileSystem _mockFileSystem;
    private readonly Fixture _fixture;

    public DedupeResultsCommandHandlerShould(ITestOutputHelper output)
    {
        _logger = new OutputLogger<DedupeResultsCommandHandler>(output);

        _mockFileSystem = Substitute.For<IFileSystem>();
        _mockFileSystem.Directory.Exists(MockDataDirectory).Returns(true);
        _mockFileSystem.Directory.EnumerateFiles(MockDataDirectory, Arg.Any<string>()).Returns(new[] { ResultsFileForMay2022 });
        _mockFileSystem.File.Exists(ResultsFileForMay2022).Returns(true);

        _fixture = new Fixture();
        _fixture.Customize<RaceResultRecord>(c => c
            .Without(x => x.Off)
            .Do(x => x.Off = new DateTime(2022, 05, 1, 13, 00, 00)));
    }

    [Fact]
    public async Task RemoveDuplicatesAndReSaveResults()
    {
        var raceResult = _fixture.Create<RaceResultRecord>();
        var clonedRaceResult = raceResult with { };
        var raceResultWithDifferentHorse = raceResult with { HorseId = raceResult.HorseId + 1 };
        var resultsWithDuplicates = new List<RaceResultRecord> { raceResult, clonedRaceResult, raceResultWithDifferentHorse };

        string? savedResultsAsCsv = null;
        _mockFileSystem.File.WriteAllTextAsync(ResultsFileForMay2022, Arg.Do<string>(x => savedResultsAsCsv = x))
            .Returns(Task.CompletedTask);
        _mockFileSystem.File.ReadAllTextAsync(ResultsFileForMay2022).Returns(Task.FromResult(await resultsWithDuplicates.ToCsvString()));

        var handler = new DedupeResultsCommandHandler(_mockFileSystem, _logger);
        var result = await handler.RunAsync(new DedupeResultsOptions { DataDirectory = MockDataDirectory });

        result.Should().Be(ExitCodes.Success);
        savedResultsAsCsv.Should().NotBeNull();
        var savedResults = await savedResultsAsCsv!.FromCsvString<RaceResultRecord>();
        savedResults.Should().BeEquivalentTo(new[] { raceResult, raceResultWithDifferentHorse });
    }
}
