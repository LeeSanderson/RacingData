using System.IO.Abstractions;
using NSubstitute;
using RaceDataDownloader.Commands.DownloadRaceCards;
using RaceDataDownloader.Tests.Fakes;
using RacePredictor.Core.RacingPost;
using RichardSzalay.MockHttp;
using Xunit.Abstractions;

namespace RaceDataDownloader.Tests.Commands.DownloadRaceCards;

[UsesVerify]
public class DownloadRaceCardsCommandHandlerShould
{
    private readonly ITestOutputHelper _output;

    public DownloadRaceCardsCommandHandlerShould(ITestOutputHelper output)
    {
        _output = output;
    }

    [Fact]
    public async Task DownloadRaceCardsAndSaveToExpectedLocation()
    {
        var mockFileSystem = Substitute.For<IFileSystem>();
        string? savedResultsAsJson = null;
        mockFileSystem.File.WriteAllTextAsync(@"c:\out\RaceCards.json", Arg.Do<string>(x => savedResultsAsJson = x))
            .Returns(Task.CompletedTask);
        string? savedResultsAsCsv = null;
        mockFileSystem.File.WriteAllTextAsync(@"c:\out\RaceCards.csv", Arg.Do<string>(x => savedResultsAsCsv = x))
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
        var logger = new OutputLogger<DownloadRaceCardsCommandHandler>(_output);

        var handler = new DownloadRaceCardsCommandHandler(mockFileSystem, httpClientFactory, clock, logger);
        var result = await handler.RunAsync(new DownloadRaceCardsOptions { OutputDirectory = @"c:\out", DateRange = "2022-06-28" });

        result.Should().Be(ExitCodes.Success);
        await Verify(savedResultsAsJson);
        await Verify(savedResultsAsCsv).UseMethodName($"{nameof(DownloadRaceCardsAndSaveToExpectedLocation)}_CSV");
    }
}