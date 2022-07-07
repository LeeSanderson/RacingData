using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using RaceDataDownloader.Models;
using RacePredictor.Core;
using RacePredictor.Core.RacingPost;
using ValidationException = System.ComponentModel.DataAnnotations.ValidationException;

namespace RaceDataDownloader.Commands.DownloadRaceCards;

public class DownloadRaceCardsCommandHandler : FileCommandHandlerBase<DownloadRaceCardsCommandHandler, DownloadRaceCardsOptions>
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly IClock _clock;

    public DownloadRaceCardsCommandHandler(
        IFileSystem fileSystem,
        IHttpClientFactory httpClientFactory,
        IClock clock,
        ILogger<DownloadRaceCardsCommandHandler> logger) : base(fileSystem, logger)
    {
        _httpClientFactory = httpClientFactory;
        _clock = clock;
    }

    protected override async Task InternalRunAsync(DownloadRaceCardsOptions options)
    {
        var (start, end, outputFolder) = ValidateOptions(options);
        var downloader = new RacingDataDownloader(_httpClientFactory, _clock);
        var raceResults = await downloader.DownloadRaceCardsInDateRange(Logger, start, end);

        await FileSystem.WriteRecordsToJsonFile(Path.Combine(outputFolder, "RaceCards.json"), raceResults);
        await FileSystem.WriteRecordsToCsvFile(
            Path.Combine(outputFolder, "RaceCards.csv"), 
            raceResults.SelectMany(RaceCardRecord.ListFrom));
    }

    private (DateOnly start, DateOnly end, string outputFolder) ValidateOptions(DownloadRaceCardsOptions options)
    {
        var range = options.DateRange ?? throw new ValidationException("Required 'dates' parameter was not provided.");
        var outputFolder = options.OutputDirectory ?? throw new ValidationException("Required 'output' parameter was not provided.");
        DateOnly start, end;
        try
        {
            (start, end) = range.ToRange();
        }
        catch (Exception e)
        {
            throw new ValidationException(e.Message);
        }

        FileSystem.CreateDirectoryIfNotExists(outputFolder);
        return (start, end, outputFolder);
    }
}