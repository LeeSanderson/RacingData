using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using RaceDataDownloader.Models;
using RacePredictor.Core.RacingPost;

namespace RaceDataDownloader.Commands.DownloadTodaysRaceCards;

public class DownloadTodaysRaceCardsCommandHandler : FileCommandHandlerBase<DownloadTodaysRaceCardsCommandHandler, DownloadTodaysRaceCardsOptions>
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly IClock _clock;

    public DownloadTodaysRaceCardsCommandHandler(
        IFileSystem fileSystem,
        IHttpClientFactory httpClientFactory,
        IClock clock,
        ILogger<DownloadTodaysRaceCardsCommandHandler> logger) : base(fileSystem, logger)
    {
        _httpClientFactory = httpClientFactory;
        _clock = clock;
    }

    protected override async Task InternalRunAsync(DownloadTodaysRaceCardsOptions options)
    {
        var dataFolder = ValidateAndCreateOutputFolder(options.DataDirectory);
        var downloader = new RacingDataDownloader(_httpClientFactory, _clock);
        var today = _clock.Today;

        var raceResults = await downloader.DownloadRaceCardsInDateRange(Logger, today, today);

        await FileSystem.WriteRecordsToCsvFile(
            Path.Combine(dataFolder, "TodaysRaceCards.csv"),
            raceResults.SelectMany(RaceCardRecord.ListFrom));
    }
}