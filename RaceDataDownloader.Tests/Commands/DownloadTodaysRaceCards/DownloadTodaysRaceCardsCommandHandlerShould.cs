using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using NSubstitute;
using RaceDataDownloader.Commands.DownloadTodaysRaceCards;
using RacePredictor.Core.RacingPost;
using Xunit.Abstractions;

namespace RaceDataDownloader.Tests.Commands.DownloadTodaysRaceCards;

public class DownloadTodaysRaceCardsCommandHandlerShould(ITestOutputHelper output)
{
    [Fact]
    public async Task FailWhenNoRaceCardsHaveGoingInformation()
    {
        var mockFileSystemBuilder = new MockFileSystemBuilder();
        var mockRacingDataDownloader = MockRacingDataDownloader
            .New()
            .MockReturnHappyValleyRaceCardUrls()
            .MockReturnHappyValleyRaceCardWithNoGoing();
        var clock = Substitute.For<IClock>();
        clock.Today.Returns(new DateOnly(2026, 05, 20));
        var logger = new OutputLogger<DownloadTodaysRaceCardsCommandHandler>(output);

        var handler = new DownloadTodaysRaceCardsCommandHandler(mockFileSystemBuilder.FileSystem, mockRacingDataDownloader, clock, logger);
        var options = new DownloadTodaysRaceCardsOptions { DataDirectory = MockFileSystemBuilder.OutputDirectory };
        var result = await handler.RunAsync(options);

        result.Should().Be(ExitCodes.Error);
    }

    [Fact]
    public async Task FailAndWriteNoCsvWhenTheRaceCardHasNoNextDataIsland()
    {
        // Capture comes from validated JSON or the run fails — there is no silent DOM fallback. An
        // absent __NEXT_DATA__ island must abort the run and leave no CSV behind.
        var mockFileSystemBuilder = new MockFileSystemBuilder();
        var mockRacingDataDownloader = MockRacingDataDownloader
            .New()
            .MockReturnHappyValleyRaceCardUrls()
            .MockReturnHappyValleyRaceCardWithNoNextData();
        var clock = Substitute.For<IClock>();
        clock.Today.Returns(new DateOnly(2026, 05, 20));
        var logger = new OutputLogger<DownloadTodaysRaceCardsCommandHandler>(output);

        var handler = new DownloadTodaysRaceCardsCommandHandler(mockFileSystemBuilder.FileSystem, mockRacingDataDownloader, clock, logger);
        var options = new DownloadTodaysRaceCardsOptions { DataDirectory = MockFileSystemBuilder.OutputDirectory };
        var result = await handler.RunAsync(options);

        result.Should().Be(ExitCodes.Error);
        mockFileSystemBuilder.TodaysSavedResultsAsCsv.Should().BeNull();
    }

    [Fact]
    public async Task DownloadRaceCardsAndSaveToExpectedLocation()
    {
        var mockFileSystemBuilder = new MockFileSystemBuilder();
        var mockRacingDataDownloader = MockRacingDataDownloader
            .New()
            .MockReturnHappyValleyRaceCardUrls()
            .MockReturnHappyValleyRaceCard();
        var clock = Substitute.For<IClock>();
        clock.Today.Returns(new DateOnly(2026, 05, 20));
        var logger = new OutputLogger<DownloadTodaysRaceCardsCommandHandler>(output);

        var handler = new DownloadTodaysRaceCardsCommandHandler(mockFileSystemBuilder.FileSystem, mockRacingDataDownloader, clock, logger);
        var options = new DownloadTodaysRaceCardsOptions { DataDirectory = MockFileSystemBuilder.OutputDirectory };
        var result = await handler.RunAsync(options);

        result.Should().Be(ExitCodes.Success);
        await Verify(mockFileSystemBuilder.TodaysSavedResultsAsCsv);
    }

    [Fact]
    public async Task WarnButStillSucceedWhenCardHasNoForecastOdds()
    {
        var mockFileSystemBuilder = new MockFileSystemBuilder();
        var mockRacingDataDownloader = MockRacingDataDownloader
            .New()
            .MockReturnHappyValleyRaceCardUrls()
            .MockReturnHappyValleyRaceCardWithNoForecast();
        var clock = Substitute.For<IClock>();
        clock.Today.Returns(new DateOnly(2026, 05, 20));
        var logger = new RecordingLogger<DownloadTodaysRaceCardsCommandHandler>(output);

        var handler = new DownloadTodaysRaceCardsCommandHandler(mockFileSystemBuilder.FileSystem, mockRacingDataDownloader, clock, logger);
        var options = new DownloadTodaysRaceCardsOptions { DataDirectory = MockFileSystemBuilder.OutputDirectory };
        var result = await handler.RunAsync(options);

        result.Should().Be(ExitCodes.Success);
        logger.Entries.Should().Contain(e => e.Level == LogLevel.Warning);
    }

    [Fact]
    public async Task WarnButStillSucceedWhenCardHasNoRatings()
    {
        var mockFileSystemBuilder = new MockFileSystemBuilder();
        var mockRacingDataDownloader = MockRacingDataDownloader
            .New()
            .MockReturnHappyValleyRaceCardUrls()
            .MockReturnHappyValleyRaceCardWithNoRatings();
        var clock = Substitute.For<IClock>();
        clock.Today.Returns(new DateOnly(2026, 05, 20));
        var logger = new RecordingLogger<DownloadTodaysRaceCardsCommandHandler>(output);

        var handler = new DownloadTodaysRaceCardsCommandHandler(mockFileSystemBuilder.FileSystem, mockRacingDataDownloader, clock, logger);
        var options = new DownloadTodaysRaceCardsOptions { DataDirectory = MockFileSystemBuilder.OutputDirectory };
        var result = await handler.RunAsync(options);

        result.Should().Be(ExitCodes.Success);
        logger.Entries.Should().Contain(e =>
            e.Level == LogLevel.Warning && e.Message.Contains("rating", StringComparison.OrdinalIgnoreCase));
    }

    [Fact]
    public async Task LogTheRatingsFillRateCountsAndNotWarnForRatingsThatArePresent()
    {
        var mockFileSystemBuilder = new MockFileSystemBuilder();
        var mockRacingDataDownloader = MockRacingDataDownloader
            .New()
            .MockReturnHappyValleyRaceCardUrls()
            .MockReturnHappyValleyRaceCard();
        var clock = Substitute.For<IClock>();
        clock.Today.Returns(new DateOnly(2026, 05, 20));
        var logger = new RecordingLogger<DownloadTodaysRaceCardsCommandHandler>(output);

        var handler = new DownloadTodaysRaceCardsCommandHandler(mockFileSystemBuilder.FileSystem, mockRacingDataDownloader, clock, logger);
        var options = new DownloadTodaysRaceCardsOptions { DataDirectory = MockFileSystemBuilder.OutputDirectory };
        var result = await handler.RunAsync(options);

        result.Should().Be(ExitCodes.Success);
        logger.Entries.Should().Contain(e =>
            e.Level == LogLevel.Information && e.Message.Contains("Pre-race ratings", StringComparison.OrdinalIgnoreCase));
        // The Happy Valley card carries OR and RPR for every runner, so neither field warns. (It has no
        // TopSpeedRating — a known per-jurisdiction gap — so a TSR warning is legitimate and not asserted against.)
        logger.Entries.Should().NotContain(e => e.Level == LogLevel.Warning && e.Message.Contains("(OR)", StringComparison.Ordinal));
        logger.Entries.Should().NotContain(e => e.Level == LogLevel.Warning && e.Message.Contains("(RPR)", StringComparison.Ordinal));
    }

    [Fact]
    public async Task LogTheForecastFillRateWithoutWarningWhenForecastsArePresent()
    {
        var mockFileSystemBuilder = new MockFileSystemBuilder();
        var mockRacingDataDownloader = MockRacingDataDownloader
            .New()
            .MockReturnHappyValleyRaceCardUrls()
            .MockReturnHappyValleyRaceCard();
        var clock = Substitute.For<IClock>();
        clock.Today.Returns(new DateOnly(2026, 05, 20));
        var logger = new RecordingLogger<DownloadTodaysRaceCardsCommandHandler>(output);

        var handler = new DownloadTodaysRaceCardsCommandHandler(mockFileSystemBuilder.FileSystem, mockRacingDataDownloader, clock, logger);
        var options = new DownloadTodaysRaceCardsOptions { DataDirectory = MockFileSystemBuilder.OutputDirectory };
        var result = await handler.RunAsync(options);

        result.Should().Be(ExitCodes.Success);
        logger.Entries.Should().Contain(e =>
            e.Level == LogLevel.Information && e.Message.Contains("forecast", StringComparison.OrdinalIgnoreCase));
        // Scoped to forecast: with forecasts present, the forecast canary must not warn. (The ratings
        // canary is exercised separately and may legitimately warn about the HK card's absent TSR.)
        logger.Entries.Should().NotContain(e =>
            e.Level == LogLevel.Warning && e.Message.Contains("forecast", StringComparison.OrdinalIgnoreCase));
    }
}
