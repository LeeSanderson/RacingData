using NSubstitute;
using RaceDataDownloader.Tests.Fakes;
using RacePredictor.Core.RacingPost;

namespace RaceDataDownloader.Tests;

internal static class MockRacingDataDownloader
{
    private const string HappyValleyRaceCardUrl = "https://www.racingpost.com/racecards/396/happy-valley/2026-05-20/920859";
    private const string RaceResultUrl = "https://www.racingpost.com/results/2022-05-11";

    public static IRacingDataDownloader New() => Substitute.For<IRacingDataDownloader>();

    public static IRacingDataDownloader MockReturnHappyValleyRaceCardUrls(this IRacingDataDownloader downloader)
    {
        var mockRaceCardUrls = new[] { HappyValleyRaceCardUrl };
        downloader
            .GetRaceCardUrls(Arg.Any<DateOnly>(), Arg.Any<DateOnly>())
            .Returns(mockRaceCardUrls.ToAsyncEnumerable());
        return downloader;
    }

    public static IRacingDataDownloader MockReturnHappyValleyRaceCard(this IRacingDataDownloader downloader)
    {
        var mockRaceCard = new RaceCardParser().Parse(FakeData.HappyValleyRaceCardFor1140RaceOn20260520);
        downloader.DownloadRaceCard(HappyValleyRaceCardUrl).Returns(mockRaceCard);
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
