using NSubstitute;
using RacePredictor.Core.RacingPost;

namespace RacePredictor.Core.Tests.RacingPost;

public class RacingDataDownloaderShould
{
    [Fact]
    public async Task ReturnExpectedListOfResultUrlsForAGivenDay()
    {
        var htmlLoader = Substitute.For<IHtmlLoader>();
        htmlLoader
            .GetHtmlResponseFrom("https://www.racingpost.com/results/2022-05-11")
            .Returns(ResourceLoader.ReadRacingPostExampleResource("daily_results_20220511.html"));
        var clock = Substitute.For<IClock>();
        var downloader = new RacingDataDownloader(htmlLoader, clock);
        var startDate = new DateOnly(2022, 05, 11);

        var urls = await downloader.GetResultUrls(startDate, startDate).ToListAsync();

        urls.Count.Should().Be(55);
        urls[0].Should().Be("https://www.racingpost.com/results/5/bath/2022-05-11/809925");
    }

    [Fact]
    public async Task ReturnExpectedListOfRaceCardUrlsForAGivenDay()
    {
        var htmlLoader = Substitute.For<IHtmlLoader>();
        htmlLoader
            .GetHtmlResponseFrom("https://www.racingpost.com/racecards/time-order/2026-05-20")
            .Returns(ResourceLoader.ReadRacingPostExampleResource("daily_racecards_timeorder_20260520.html"));
        var clock = Substitute.For<IClock>();
        var downloader = new RacingDataDownloader(htmlLoader, clock);
        var startDate = new DateOnly(2026, 05, 20);

        var urls = await downloader.GetRaceCardUrls(startDate, startDate).ToListAsync();

        urls.Count.Should().Be(50);
        urls[0].Should().Be("https://www.racingpost.com/racecards/396/happy-valley/2026-05-20/920859/");
    }
}
