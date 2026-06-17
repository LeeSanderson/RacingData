using System.IO.Abstractions;
using AutoFixture;
using NSubstitute;
using RaceDataDownloader.Commands;
using RaceDataDownloader.Commands.DedupeResults;
using RaceDataDownloader.Commands.FixRaceIds;
using RaceDataDownloader.Models;
using Xunit.Abstractions;

namespace RaceDataDownloader.Tests.Commands.FixRaceIds;

public class FixRaceIdsCommandHandlerShould
{
    private const string MockDataDirectory = @"c:\out";
    private const string ResultsFileForMay2022 = @"c:\out\Results_202205.csv";

    private readonly OutputLogger<FixRaceIdsCommandHandler> _logger;
    private readonly IFileSystem _mockFileSystem;
    private readonly Fixture _fixture;

    public FixRaceIdsCommandHandlerShould(ITestOutputHelper output)
    {
        _logger = new OutputLogger<FixRaceIdsCommandHandler>(output);

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
    public async Task ReplaceRaceIdInResultsWhereRaceIdEqualsCourseId()
    {
        var raceResult = _fixture.Create<RaceResultRecord>();
        var badRaceResult = raceResult with { RaceId = raceResult.CourseId };

        // 27,523,500 is the unique ID generated as minutes since 1970 from 2022-05-01 13:00:00
        var correctedRaceResult = raceResult with { RaceId = 27_523_500 };
        var resultsWithBadRaceId = new List<RaceResultRecord> { raceResult, badRaceResult };

        string? savedResultsAsCsv = null;
        _mockFileSystem.File.WriteAllTextAsync(ResultsFileForMay2022, Arg.Do<string>(x => savedResultsAsCsv = x))
            .Returns(Task.CompletedTask);
        _mockFileSystem.File.ReadAllTextAsync(ResultsFileForMay2022).Returns(Task.FromResult(await resultsWithBadRaceId.ToCsvString()));

        var handler = new FixRaceIdsCommandHandler(_mockFileSystem, _logger);
        var result = await handler.RunAsync(new FixRaceIdsOptions { DataDirectory = MockDataDirectory });

        result.Should().Be(ExitCodes.Success);
        savedResultsAsCsv.Should().NotBeNull();
        var savedResults = await savedResultsAsCsv!.FromCsvString<RaceResultRecord>();
        savedResults.Should().BeEquivalentTo([raceResult, correctedRaceResult]);
    }
}
