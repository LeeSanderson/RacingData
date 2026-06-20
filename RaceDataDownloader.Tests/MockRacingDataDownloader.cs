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

    public static IRacingDataDownloader MockReturnHappyValleyRaceCardWithNoGoing(this IRacingDataDownloader downloader)
    {
        var html = FakeData.HappyValleyRaceCardFor1140RaceOn20260520
            .Replace("data-testid=\"Link__Going\"", "data-testid=\"Link__GoingRemoved\"", StringComparison.Ordinal);
        var mockRaceCard = new RaceCardParser().Parse(html);
        downloader.DownloadRaceCard(HappyValleyRaceCardUrl).Returns(mockRaceCard);
        return downloader;
    }

    public static IRacingDataDownloader MockReturnHappyValleyRaceCardWithNoForecast(this IRacingDataDownloader downloader)
    {
        var html = FakeData.HappyValleyRaceCardFor1140RaceOn20260520
            .Replace("data-testid=\"Link__BettingForecastHorse\"", "data-testid=\"Link__BettingForecastHorseRemoved\"", StringComparison.Ordinal);
        var mockRaceCard = new RaceCardParser().Parse(html);
        downloader.DownloadRaceCard(HappyValleyRaceCardUrl).Returns(mockRaceCard);
        return downloader;
    }

    public static IRacingDataDownloader MockReturnHappyValleyRaceCardWithNoRatings(this IRacingDataDownloader downloader)
    {
        // Remove the runner-stats containers so OR/RPR/TSR all parse as null, exercising the ratings canary.
        var html = FakeData.HappyValleyRaceCardFor1140RaceOn20260520
            .Replace("data-testid=\"Container__RunnerStats\"", "data-testid=\"Container__RunnerStatsRemoved\"", StringComparison.Ordinal);
        var mockRaceCard = new RaceCardParser().Parse(html);
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
