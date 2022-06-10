using NSubstitute;
using RacePredictor.Core.RacingPost;
using RichardSzalay.MockHttp;

namespace RacePredictor.Core.Tests.RacingPost;

public class RacingDataDownloaderShould
{
    [Fact]
    public async Task ReturnExpectedListOfResultUrlsForAGivenDay()
    {
        var mockHttpMessageHandler = new MockHttpMessageHandler();
        mockHttpMessageHandler.When(HttpMethod.Get, "https://www.racingpost.com/results/2022-05-11")
            .Respond("text/html", ResourceLoader.ReadResource("daily_results_20220511.html"));

        var httpClientFactory = Substitute.For<IHttpClientFactory>();
        httpClientFactory.CreateClient(Arg.Any<string>()).Returns(new HttpClient(mockHttpMessageHandler));
        var downloader = new RacingDataDownloader(httpClientFactory);
        var startDate = new DateOnly(2022, 05, 11);

        var urls = await downloader.GetResultUrls(startDate, startDate).ToListAsync();

        urls.Count.Should().Be(57);
        urls[0].Should().Be("https://www.racingpost.com/results/5/bath/2022-05-11/809925");
    }
}