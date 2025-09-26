using System.IO.Abstractions;
using NSubstitute;
using RaceDataDownloader.Commands.DownloadTodaysRaceCards;
using RaceDataDownloader.Tests.Fakes;
using RacePredictor.Core.RacingPost;
using RichardSzalay.MockHttp;
using Xunit.Abstractions;

namespace RaceDataDownloader.Tests.Commands.DownloadTodaysRaceCards;

public class DownloadTodaysRaceCardsCommandHandlerShould
{
    private readonly ITestOutputHelper _output;

    public DownloadTodaysRaceCardsCommandHandlerShould(ITestOutputHelper output)
    {
        _output = output;
    }

    [Fact]
    public async Task DownloadRaceCardsAndSaveToExpectedLocation()
    {
        var mockFileSystem = Substitute.For<IFileSystem>();
        string? savedResultsAsCsv = null;
        mockFileSystem.File.WriteAllTextAsync(@"c:\out\TodaysRaceCards.csv", Arg.Do<string>(x => savedResultsAsCsv = x))
            .Returns(Task.CompletedTask);
        mockFileSystem.Directory.Exists(@"c:\out").Returns(true);

        var mockHttpMessageHandler = new MockHttpMessageHandler();
        mockHttpMessageHandler.When(HttpMethod.Get, "https://www.racingpost.com/racecards/2022-06-28")
            .Respond("text/html", FakeData.DailyRaceCardsFor20220628);
        mockHttpMessageHandler.When(HttpMethod.Get, "https://www.racingpost.com/racecards/22/hamilton/2022-06-28/813803")
            .Respond("text/html", FakeData.HamiltonRaceCardFor1315RaceOn20220628);

        var httpClientFactory = Substitute.For<IHttpClientFactory>();
        httpClientFactory.CreateClient(Arg.Any<string>()).Returns(new HttpClient(mockHttpMessageHandler));
        var clock = Substitute.For<IClock>();
        clock.Today.Returns(new DateOnly(2022, 06, 28));
        var logger = new OutputLogger<DownloadTodaysRaceCardsCommandHandler>(_output);

        var handler = new DownloadTodaysRaceCardsCommandHandler(mockFileSystem, httpClientFactory, clock, logger);
        var result = await handler.RunAsync(new DownloadTodaysRaceCardsOptions { DataDirectory = @"c:\out" });

        result.Should().Be(ExitCodes.Success);
        await Verify(savedResultsAsCsv);
    }
}
