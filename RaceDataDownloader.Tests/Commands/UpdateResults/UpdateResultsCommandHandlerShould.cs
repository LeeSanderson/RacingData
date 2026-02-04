using NSubstitute;
using RaceDataDownloader.Commands;
using RaceDataDownloader.Commands.UpdateResults;
using RaceDataDownloader.Models;
using RacePredictor.Core.RacingPost;
using Xunit.Abstractions;

namespace RaceDataDownloader.Tests.Commands.UpdateResults;

public class UpdateResultsCommandHandlerShould : IAsyncLifetime
{
    private const string ResultsFileForMay2022 = @"c:\out\Results_202205.csv";
    private const string ResultsFileForApril2022 = @"c:\out\Results_202204.csv";
    private const string ResultsFileForMarch2022 = @"c:\out\Results_202203.csv";

    private readonly OutputLogger<UpdateResultsCommandHandler> _logger;
    private readonly IClock _clock;
    private readonly MockFileSystemBuilder _mockFileSystemBuilder;
    private IRacingDataDownloader _mockRacingDataDownloader = null!;

    public UpdateResultsCommandHandlerShould(ITestOutputHelper output)
    {
        _logger = new OutputLogger<UpdateResultsCommandHandler>(output);
        _clock = Substitute.For<IClock>();
        _clock.Today.Returns(new DateOnly(2022, 05, 12));
        _mockFileSystemBuilder = new MockFileSystemBuilder();
    }

    public async Task InitializeAsync() =>
        _mockRacingDataDownloader = await MockRacingDataDownloader
            .New()
            .MockRaceResultUrls()
            .MockReturnBathRaceResults();

    public Task DisposeAsync() => Task.CompletedTask;

    [Fact]
    public async Task DownloadResultsWhenNoResultsExist()
    {
        var result = await ExecuteHandler(1);

        result.Should().Be(ExitCodes.Success);
        await Verify(_mockFileSystemBuilder.GetContent(ResultsFileForMay2022));
    }

    [Fact]
    public async Task SkipDownloadWhenResultsAlreadyExist()
    {
        _mockFileSystemBuilder.FileSystem.File.Exists(ResultsFileForMay2022).Returns(true);
        await AddFakeResultsFile(ResultsFileForMay2022, 2022, 05, 11, 11);
    
        var result = await ExecuteHandler(1);

        result.Should().Be(ExitCodes.Success);
        await _mockFileSystemBuilder.FileSystem.File.DidNotReceive().WriteAllTextAsync(ResultsFileForMay2022, Arg.Any<string>());
    }
    
    [Fact]
    public async Task BackFillDataForThe11ThWhenGetting2DaysOfDataAndTodayIs13ThAndHaveExistingDataFor12Th()
    {
        _clock.Today.Returns(new DateOnly(2022, 05, 13));
        _mockFileSystemBuilder.FileSystem.File.Exists(ResultsFileForMay2022).Returns(true, true, false, true);
        await AddFakeResultsFile(ResultsFileForMay2022, 2022, 05, 12, 12);
    
        var result = await ExecuteHandler(2);

        result.Should().Be(ExitCodes.Success);
        await Verify(_mockFileSystemBuilder.GetContent(ResultsFileForMay2022));
    }
    
    [Fact]
    public async Task FillInDataForThe11ThWhenGetting2DaysOfDataAndTodayIs12ThAndHaveExistingDataFor10Th()
    {
        _clock.Today.Returns(new DateOnly(2022, 05, 12));
        _mockFileSystemBuilder.FileSystem.File.Exists(ResultsFileForMay2022).Returns(true, true, false, true);
        await AddFakeResultsFile(ResultsFileForMay2022, 2022, 05, 10, 10);

        var result = await ExecuteHandler(2);

        result.Should().Be(ExitCodes.Success);
        await Verify(_mockFileSystemBuilder.GetContent(ResultsFileForMay2022));
    }


    [Fact]
    public async Task SkipDownloadOverMultipleMonthsWhenResultsAlreadyExist()
    {
        _clock.Today.Returns(new DateOnly(2022, 05, 31));
    
        _mockFileSystemBuilder.FileSystem.File.Exists(ResultsFileForMarch2022).Returns(true);
        _mockFileSystemBuilder.FileSystem.File.Exists(ResultsFileForApril2022).Returns(true);
        _mockFileSystemBuilder.FileSystem.File.Exists(ResultsFileForMay2022).Returns(true);
    
        await AddFakeResultsFile(ResultsFileForMarch2022, 2022, 03, 01, 31);
        await AddFakeResultsFile(ResultsFileForApril2022, 2022, 04, 01, 30);
        await AddFakeResultsFile(ResultsFileForMay2022, 2022, 05, 01, 31);
        
        var result = await ExecuteHandler(90);

        result.Should().Be(ExitCodes.Success);
        await _mockFileSystemBuilder.FileSystem.File.DidNotReceive().WriteAllTextAsync(Arg.Any<string>(), Arg.Any<string>());
    }

    private async Task<int> ExecuteHandler(int minimumPeriodInDays)
    {
        var handler = new UpdateResultsCommandHandler(_mockFileSystemBuilder.FileSystem, _mockRacingDataDownloader, _clock, _logger);
        var options = new UpdateResultsOptions { DataDirectory = MockFileSystemBuilder.OutputDirectory, MinimumPeriodInDays = minimumPeriodInDays };
        var result = await handler.RunAsync(options);
        return result;
    }

    private async Task AddFakeResultsFile(string fileName, int year, int month, int startDay, int endDay)
    {
        var existingResults = new List<RaceResultRecord> { new() { Off = new DateTime(year, month, startDay, 13, 50, 00) } };
        if (startDay != endDay)
        {
            existingResults.Add(new RaceResultRecord { Off = new DateTime(year, month, endDay, 13, 50, 00) });
        }
    
        _mockFileSystemBuilder
            .FileSystem
            .File
            .ReadAllTextAsync(fileName)
            .Returns(Task.FromResult(await existingResults.ToCsvString()));
    }
}
