using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using RaceDataDownloader.Models;
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

        await FileSystem.WriteRecordsToCsvFile(
            Path.Combine(dataFolder, "TodaysRaceCards.csv"),
            raceResults.SelectMany(RaceCardRecord.ListFrom));
    }
}
