using NSubstitute;
using RaceDataDownloader.Tests.Fakes;
using RacePredictor.Core.RacingPost;

namespace RaceDataDownloader.Tests;

internal static class MockRacingDataDownloader
{
    private const string HamiltonRaceCardUrl = "https://www.racingpost.com/racecards/22/hamilton/2022-06-28/813803";
    private const string RaceResultUrl = "https://www.racingpost.com/results/2022-05-11";

    public static IRacingDataDownloader New() => Substitute.For<IRacingDataDownloader>();

    public static IRacingDataDownloader MockReturnHamiltonRaceCardUrls(this IRacingDataDownloader downloader)
    {
        var mockRaceCardUrls = new[] { HamiltonRaceCardUrl };
        downloader
            .GetRaceCardUrls(Arg.Any<DateOnly>(), Arg.Any<DateOnly>())
            .Returns(mockRaceCardUrls.ToAsyncEnumerable());
        return downloader;
    }

    public static IRacingDataDownloader MockReturnHamiltonRaceCard(this IRacingDataDownloader downloader)
    {
        var mockRaceCard = new RaceCardParser().Parse(FakeData.HamiltonRaceCardFor1315RaceOn20220628);
        downloader.DownloadRaceCard(HamiltonRaceCardUrl).Returns(mockRaceCard);
        return downloader;
    }

    public static IRacingDataDownloader MockRaceResultUrls(this IRacingDataDownloader downloader)
    {
        var mockRaceResultUrls = new[] { RaceResultUrl };
        downloader.GetResultUrls(Arg.Any<DateOnly>(), Arg.Any<DateOnly>())
            .Returns(mockRaceResultUrls.ToAsyncEnumerable());
        return downloader;
    }

    public static async Task<IRacingDataDownloader> MockReturnBathRaceResults(this IRacingDataDownloader downloader)
    {
        var parser = new RacingResultParser();
        var mockedRaceResult = await parser.Parse(FakeData.BathRaceResultFor1730RaceOn20220511);

        downloader.DownloadResults(RaceResultUrl).Returns(mockedRaceResult);
        return downloader;
    }
}
