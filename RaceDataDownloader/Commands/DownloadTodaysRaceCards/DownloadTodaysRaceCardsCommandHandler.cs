using System.ComponentModel.DataAnnotations;
using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using RaceDataDownloader.Models;
using RacePredictor.Core;
using RacePredictor.Core.RacingPost;

namespace RaceDataDownloader.Commands.DownloadTodaysRaceCards;

public class DownloadTodaysRaceCardsCommandHandler(
    IFileSystem fileSystem,
    IRacingDataDownloader downloader,
    IClock clock,
    ILogger<DownloadTodaysRaceCardsCommandHandler> logger)
    : FileCommandHandlerBase<DownloadTodaysRaceCardsCommandHandler, DownloadTodaysRaceCardsOptions>(fileSystem, logger)
{
    protected override async Task InternalRunAsync(DownloadTodaysRaceCardsOptions options)
    {
        var dataFolder = ValidateAndCreateOutputFolder(options.DataDirectory);
        var today = clock.Today;

        var raceResults = await downloader.DownloadRaceCardsInDateRange(Logger, today, today);

        EnsureGoingDataIsPresent(raceResults);
        LogForecastFillRate(raceResults);

        await FileSystem.WriteRecordsToCsvFile(
            Path.Combine(dataFolder, "TodaysRaceCards.csv"),
            raceResults.SelectMany(RaceCardRecord.ListFrom));
    }

    // Soft canary for a Racing Post betting-forecast markup change: log how many runners got a forecast
    // and warn (never throw) when a non-empty card yields none. A non-null DecimalOdds marks a real
    // forecast; runners left at the "SP" default don't count -- same predicate the validate merge uses.
    private void LogForecastFillRate(List<RaceCard> raceCards)
    {
        var totalRunners = raceCards.Sum(c => c.Runners.Length);
        if (totalRunners == 0)
        {
            return;
        }

        var withForecast = raceCards.Sum(c => c.Runners.Count(r => r.Statistics.Odds.DecimalOdds.HasValue));
        Logger.LogInformation("Forecast odds present for {WithForecast} of {Total} runners.", withForecast, totalRunners);

        if (withForecast == 0)
        {
            Logger.LogWarning(
                "No runners across the {CardCount} downloaded race card(s) have forecast odds. " +
                "The Racing Post betting-forecast structure may have changed.",
                raceCards.Count);
        }
    }

    private static void EnsureGoingDataIsPresent(List<RaceCard> raceCards)
    {
        if (raceCards.Count > 0 && raceCards.All(r => string.IsNullOrEmpty(r.Attributes.Going)))
        {
            throw new ValidationException(
                $"None of the {raceCards.Count} downloaded race cards has going information. " +
                "The Racing Post page structure may have changed.");
        }
    }
}
