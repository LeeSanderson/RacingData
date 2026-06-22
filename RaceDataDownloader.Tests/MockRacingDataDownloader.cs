using System.Text.RegularExpressions;
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
        // Capture now reads forecast odds from the JSON island, so neutralise the forecast there as
        // well as in the DOM oracle. A card with no forecast leaves every runner at SP (exercising the
        // forecast canary) while the two readings still agree, so cross-validation does not abort.
        var html = FakeData.HappyValleyRaceCardFor1140RaceOn20260520
            .Replace("\"bettingForecast\":", "\"bettingForecastRemoved\":", StringComparison.Ordinal)
            .Replace("data-testid=\"Link__BettingForecastHorse\"", "data-testid=\"Link__BettingForecastHorseRemoved\"", StringComparison.Ordinal);
        var mockRaceCard = new RaceCardParser().Parse(html);
        downloader.DownloadRaceCard(HappyValleyRaceCardUrl).Returns(mockRaceCard);
        return downloader;
    }

    public static IRacingDataDownloader MockReturnHappyValleyRaceCardWithNoRatings(this IRacingDataDownloader downloader)
    {
        // Null the runner ratings in the JSON island (the captured source) and remove the DOM
        // runner-stats containers, so OR/RPR/TSR all parse as null on both readings. This exercises the
        // ratings canary without tripping cross-validation (both readings agree the ratings are absent).
        var html = FakeData.HappyValleyRaceCardFor1140RaceOn20260520
            .Replace("data-testid=\"Container__RunnerStats\"", "data-testid=\"Container__RunnerStatsRemoved\"", StringComparison.Ordinal);
        html = Regex.Replace(html, "\"(officialRatingToday|rpPostmark|rpTopspeed)\":-?\\d+", "\"$1\":\"-\"");
        var mockRaceCard = new RaceCardParser().Parse(html);
        downloader.DownloadRaceCard(HappyValleyRaceCardUrl).Returns(mockRaceCard);
        return downloader;
    }

    public static IRacingDataDownloader MockReturnHappyValleyRaceCardWithNoNextData(this IRacingDataDownloader downloader)
    {
        // Remove the __NEXT_DATA__ JSON island entirely. Parsing is deferred to call time (a lazy
        // Returns callback) so the reader's fail-loud ValidationException is thrown inside RunAsync
        // rather than at mock-setup time.
        var html = FakeData.HappyValleyRaceCardFor1140RaceOn20260520
            .Replace("__NEXT_DATA__", "__NEXT_DATA_REMOVED__", StringComparison.Ordinal);
        downloader.DownloadRaceCard(HappyValleyRaceCardUrl).Returns(_ => new RaceCardParser().Parse(html));
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
