using System.IO.Abstractions;
using NSubstitute;
using RaceDataDownloader.Commands;
using RaceDataDownloader.Commands.UpdateResults;
using RaceDataDownloader.Models;
using RaceDataDownloader.Tests.Fakes;
using RacePredictor.Core.RacingPost;
using RichardSzalay.MockHttp;
using Xunit.Abstractions;

namespace RaceDataDownloader.Tests.Commands.UpdateResults;

[UsesVerify]
public class UpdateResultsCommandHandlerShould
{
    private const string MockDataDirectory = @"c:\out";
    private const string ResultsFileForMay2022 = @"c:\out\Results_202205.csv";
    private const string ResultsFileForApril2022 = @"c:\out\Results_202204.csv";
    private const string ResultsFileForMarch2022 = @"c:\out\Results_202203.csv";

    private readonly IHttpClientFactory _httpClientFactory;
    private readonly OutputLogger<UpdateResultsCommandHandler> _logger;
    private readonly IClock _clock;
    private readonly IFileSystem _mockFileSystem;

    public UpdateResultsCommandHandlerShould(ITestOutputHelper output)
    {
        _logger = new OutputLogger<UpdateResultsCommandHandler>(output);

        var mockHttpMessageHandler = new MockHttpMessageHandler();
        mockHttpMessageHandler.When(HttpMethod.Get, "https://www.racingpost.com/results/2022-05-11")
            .Respond("text/html", FakeData.DailyResultsFor20220511);
        mockHttpMessageHandler.When(HttpMethod.Get, "https://www.racingpost.com/results/5/bath/2022-05-11/809925")
            .Respond("text/html", FakeData.BathRaceResultFor1730RaceOn20220511);

        _httpClientFactory = Substitute.For<IHttpClientFactory>();
        _httpClientFactory.CreateClient(Arg.Any<string>()).Returns(new HttpClient(mockHttpMessageHandler));

        _clock = Substitute.For<IClock>();
        _clock.Today.Returns(new DateOnly(2022, 05, 12));

        _mockFileSystem = Substitute.For<IFileSystem>();
        _mockFileSystem.Directory.Exists(MockDataDirectory).Returns(true);
    }

    [Fact]
    public async Task DownloadResultsWhenNoResultsExist()
    {
        string? savedResultsAsCsv = null;
        _mockFileSystem.File.WriteAllTextAsync(ResultsFileForMay2022, Arg.Do<string>(x => savedResultsAsCsv = x))
            .Returns(Task.CompletedTask);
        _mockFileSystem.File.Exists(ResultsFileForMay2022).Returns(false);

        var handler = new UpdateResultsCommandHandler(_mockFileSystem, _httpClientFactory, _clock, _logger);
        var result = await handler.RunAsync(new UpdateResultsOptions { DataDirectory = MockDataDirectory, MinimumPeriodInDays = 1 });

        result.Should().Be(ExitCodes.Success);
        await Verify(savedResultsAsCsv);
    }

    [Fact]
    public async Task SkipDownloadWhenResultsAlreadyExist()
    {
        _mockFileSystem.File.Exists(ResultsFileForMay2022).Returns(true);
        await AddFakeResultsFile(ResultsFileForMay2022, 2022, 05, 11, 11);

        var handler = new UpdateResultsCommandHandler(_mockFileSystem, _httpClientFactory, _clock, _logger);
        var result = await handler.RunAsync(new UpdateResultsOptions { DataDirectory = MockDataDirectory, MinimumPeriodInDays = 1 });

        result.Should().Be(ExitCodes.Success);
        await _mockFileSystem.File.DidNotReceive().WriteAllTextAsync(ResultsFileForMay2022, Arg.Any<string>());
    }

    [Fact]
    public async Task BackFillDataForThe11ThWhenGetting2DaysOfDataAndTodayIs13ThAndHaveExistingDataFor12Th()
    {
        _clock.Today.Returns(new DateOnly(2022, 05, 13));

        string? savedResultsAsCsv = null;
        _mockFileSystem.File.WriteAllTextAsync(ResultsFileForMay2022, Arg.Do<string>(x => savedResultsAsCsv = x))
            .Returns(Task.CompletedTask);

        _mockFileSystem.File.Exists(ResultsFileForMay2022).Returns(true, true, false, true);
        await AddFakeResultsFile(ResultsFileForMay2022, 2022, 05, 12, 12);

        var handler = new UpdateResultsCommandHandler(_mockFileSystem, _httpClientFactory, _clock, _logger);
        var result = await handler.RunAsync(new UpdateResultsOptions { DataDirectory = MockDataDirectory, MinimumPeriodInDays = 2 });

        result.Should().Be(ExitCodes.Success);
        await Verify(savedResultsAsCsv);
    }

    [Fact]
    public async Task FillInDataForThe11ThWhenGetting2DaysOfDataAndTodayIs12ThAndHaveExistingDataFor10Th()
    {
        _clock.Today.Returns(new DateOnly(2022, 05, 12));

        string? savedResultsAsCsv = null;
        _mockFileSystem.File.WriteAllTextAsync(ResultsFileForMay2022, Arg.Do<string>(x => savedResultsAsCsv = x))
            .Returns(Task.CompletedTask);

        _mockFileSystem.File.Exists(ResultsFileForMay2022).Returns(true, true, false, true);
        await AddFakeResultsFile(ResultsFileForMay2022, 2022, 05, 10, 10);

        var handler = new UpdateResultsCommandHandler(_mockFileSystem, _httpClientFactory, _clock, _logger);
        var result = await handler.RunAsync(new UpdateResultsOptions { DataDirectory = MockDataDirectory, MinimumPeriodInDays = 2 });

        result.Should().Be(ExitCodes.Success);
        await Verify(savedResultsAsCsv);
    }


    [Fact]
    public async Task SkipDownloadOverMultipleMonthsWhenResultsAlreadyExist()
    {
        _clock.Today.Returns(new DateOnly(2022, 05, 31));

        _mockFileSystem.File.Exists(ResultsFileForMarch2022).Returns(true);
        _mockFileSystem.File.Exists(ResultsFileForApril2022).Returns(true);
        _mockFileSystem.File.Exists(ResultsFileForMay2022).Returns(true);

        await AddFakeResultsFile(ResultsFileForMarch2022, 2022, 03, 01, 31);
        await AddFakeResultsFile(ResultsFileForApril2022, 2022, 04, 01, 30);
        await AddFakeResultsFile(ResultsFileForMay2022, 2022, 05, 01, 31);

        var handler = new UpdateResultsCommandHandler(_mockFileSystem, _httpClientFactory, _clock, _logger);
        var result = await handler.RunAsync(new UpdateResultsOptions { DataDirectory = MockDataDirectory, MinimumPeriodInDays = 90 });

        result.Should().Be(ExitCodes.Success);
        await _mockFileSystem.File.DidNotReceive().WriteAllTextAsync(Arg.Any<string>(), Arg.Any<string>());
    }

    private async Task AddFakeResultsFile(string fileName, int year, int month, int startDay, int endDay)
    {
        var existingResults = new List<RaceResultRecord> { new() { Off = new DateTime(year, month, startDay, 13, 50, 00) } };
        if (startDay != endDay)
        {
            existingResults.Add(new RaceResultRecord { Off = new DateTime(year, month, endDay, 13, 50, 00) });
        }

        _mockFileSystem.File.ReadAllTextAsync(fileName).Returns(Task.FromResult(await existingResults.ToCsvString()));
    }
}