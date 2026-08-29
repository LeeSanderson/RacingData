using System.ComponentModel.DataAnnotations;
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
            .GetHtmlResponseFrom("https://www.racingpost.com/results/2026-08-28/time-order")
            .Returns(ResourceLoader.ReadRacingPostExampleResource("daily_results_timeorder_20260828.html"));
        var clock = Substitute.For<IClock>();
        var downloader = new RacingDataDownloader(htmlLoader, clock);
        var startDate = new DateOnly(2026, 08, 28);

        var urls = await downloader.GetResultUrls(startDate, startDate).ToListAsync();

        urls.Count.Should().Be(50);
        urls[0].Should().Be("https://www.racingpost.com/results/180/down-royal/2026-08-28/927303");
    }

    [Fact]
    public async Task ReturnNoResultUrlsOnChristmasDayWhenThereIsNoRacing()
    {
        var htmlLoader = Substitute.For<IHtmlLoader>();
        htmlLoader
            .GetHtmlResponseFrom("https://www.racingpost.com/results/2025-12-25/time-order")
            .Returns(ResourceLoader.ReadRacingPostExampleResource("daily_results_timeorder_20251225_no_racing.html"));
        var clock = Substitute.For<IClock>();
        var downloader = new RacingDataDownloader(htmlLoader, clock);
        var startDate = new DateOnly(2025, 12, 25);

        var urls = await downloader.GetResultUrls(startDate, startDate).ToListAsync();

        urls.Should().BeEmpty();
    }

    [Fact]
    public async Task ThrowWhenADateThatShouldHaveRacingYieldsNoResultUrls()
    {
        var htmlLoader = Substitute.For<IHtmlLoader>();
        htmlLoader
            .GetHtmlResponseFrom("https://www.racingpost.com/results/2026-08-26/time-order")
            .Returns(ResourceLoader.ReadRacingPostExampleResource("daily_results_timeorder_20251225_no_racing.html"));
        var clock = Substitute.For<IClock>();
        var downloader = new RacingDataDownloader(htmlLoader, clock);
        var startDate = new DateOnly(2026, 08, 26);

        var getUrls = async () => await downloader.GetResultUrls(startDate, startDate).ToListAsync();

        await getUrls.Should().ThrowAsync<ValidationException>().WithMessage("*results/2026-08-26/time-order*");
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
