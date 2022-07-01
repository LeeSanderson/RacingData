using System.IO.Abstractions;
using NSubstitute;
using RaceDataDownloader.Commands.UpdateResults;
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
    }

    [Fact]
    public async Task DownloadResultsWhenNoResultsExist()
    {
        var clock = Substitute.For<IClock>();
        clock.Today.Returns(new DateOnly(2022, 05, 12));

        var mockFileSystem = Substitute.For<IFileSystem>();
        string? savedResultsAsCsv = null;
        mockFileSystem.File.WriteAllTextAsync(ResultsFileForMay2022, Arg.Do<string>(x => savedResultsAsCsv = x))
            .Returns(Task.CompletedTask);
        mockFileSystem.Directory.Exists(MockDataDirectory).Returns(true);
        mockFileSystem.File.Exists(ResultsFileForMay2022).Returns(true);

        var handler = new UpdateResultsCommandHandler(mockFileSystem, _httpClientFactory, clock, _logger);
        var result = await handler.RunAsync(new UpdateResultsOptions { DataDirectory = MockDataDirectory, MinimumPeriodInDays = 1 });

        result.Should().Be(ExitCodes.Success);
        await Verify(savedResultsAsCsv);
    }
}