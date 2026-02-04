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
            .GetHtmlResponseFrom("https://www.racingpost.com/racecards/2022-06-28")
            .Returns(ResourceLoader.ReadRacingPostExampleResource("daily_racecards_20220628.html"));
        var clock = Substitute.For<IClock>();
        var downloader = new RacingDataDownloader(htmlLoader, clock);
        var startDate = new DateOnly(2022, 06, 28);

        var urls = await downloader.GetRaceCardUrls(startDate, startDate).ToListAsync();

        urls.Count.Should().Be(44);
        urls[0].Should().Be("https://www.racingpost.com/racecards/22/hamilton/2022-06-28/813803");
    }
}
