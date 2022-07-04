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
        var existingResults = new[] {new RaceResultRecord { Off = new DateTime(2022, 05, 11, 13, 50, 00)}};
        _mockFileSystem.File.ReadAllTextAsync(ResultsFileForMay2022).Returns(Task.FromResult(await existingResults.ToCsvString()));

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
        var existingResults = new[] { new RaceResultRecord { Off = new DateTime(2022, 05, 12, 13, 50, 00) } };
        _mockFileSystem.File.ReadAllTextAsync(ResultsFileForMay2022).Returns(Task.FromResult(await existingResults.ToCsvString()));

        var handler = new UpdateResultsCommandHandler(_mockFileSystem, _httpClientFactory, _clock, _logger);
        var result = await handler.RunAsync(new UpdateResultsOptions { DataDirectory = MockDataDirectory, MinimumPeriodInDays = 2 });

        result.Should().Be(ExitCodes.Success);
        await Verify(savedResultsAsCsv);
    }
}