using System.IO.Abstractions;
using NSubstitute;
using RaceDataDownloader.Commands.DownloadResults;
using RaceDataDownloader.Tests.Fakes;
using RacePredictor.Core.RacingPost;
using RichardSzalay.MockHttp;
using Xunit.Abstractions;

namespace RaceDataDownloader.Tests.Commands.DownloadResults;

public class DownloadResultsCommandHandlerShould
{
    private readonly ITestOutputHelper _output;

    public DownloadResultsCommandHandlerShould(ITestOutputHelper output)
    {
        _output = output;
    }

    [Fact]
    public async Task DownloadResultsAndSaveToExpectedLocation()
    {
        var mockFileSystem = Substitute.For<IFileSystem>();
        string? savedResultsAsJson = null;
        mockFileSystem.File.WriteAllTextAsync(@"c:\out\Results.json", Arg.Do<string>(x => savedResultsAsJson = x))
            .Returns(Task.CompletedTask);
        string? savedResultsAsCsv = null;
        mockFileSystem.File.WriteAllTextAsync(@"c:\out\Results.csv", Arg.Do<string>(x => savedResultsAsCsv = x))
            .Returns(Task.CompletedTask);
        mockFileSystem.Directory.Exists(@"c:\out").Returns(true);

        var mockHttpMessageHandler = new MockHttpMessageHandler();
        mockHttpMessageHandler.When(HttpMethod.Get, "https://www.racingpost.com/results/2022-05-11")
            .Respond("text/html", FakeData.DailyResultsFor20220511);
        mockHttpMessageHandler.When(HttpMethod.Get, "https://www.racingpost.com/results/5/bath/2022-05-11/809925")
            .Respond("text/html", FakeData.BathRaceResultFor1730RaceOn20220511);

        var httpClientFactory = Substitute.For<IHttpClientFactory>();
        httpClientFactory.CreateClient(Arg.Any<string>()).Returns(new HttpClient(mockHttpMessageHandler));

        var clock = Substitute.For<IClock>();

        var logger = new OutputLogger<DownloadResultsCommandHandler>(_output);

        var handler = new DownloadResultsCommandHandler(mockFileSystem, httpClientFactory, clock, logger);
        var result = await handler.RunAsync(new DownloadResultsOptions { OutputDirectory = @"c:\out", DateRange = "2022-05-11" });

        result.Should().Be(ExitCodes.Success);
        await Verify(savedResultsAsJson);
        await Verify(savedResultsAsCsv).UseMethodName($"{nameof(DownloadResultsAndSaveToExpectedLocation)}_CSV");
    }
}
