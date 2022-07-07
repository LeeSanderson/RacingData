using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using RaceDataDownloader.Models;
using RacePredictor.Core.RacingPost;

namespace RaceDataDownloader.Commands.DownloadResults;

public class DownloadResultsCommandHandler : FileCommandHandlerBase<DownloadResultsCommandHandler, DownloadResultsOptions>
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly IClock _clock;
    
    public DownloadResultsCommandHandler(
        IFileSystem fileSystem,
        IHttpClientFactory httpClientFactory,
        IClock clock,
        ILogger<DownloadResultsCommandHandler> logger) : base(fileSystem, logger)
    {
        _httpClientFactory = httpClientFactory;
        _clock = clock;
    }

    protected override async Task InternalRunAsync(DownloadResultsOptions options)
    {
        var (start, end, outputFolder) = ValidateOptions(options);
        var downloader = new RacingDataDownloader(_httpClientFactory, _clock);
        var raceResults = await downloader.DownloadRaceResultsInRange(Logger, start, end);

        await FileSystem.WriteRecordsToJsonFile(Path.Combine(outputFolder, "Results.json"), raceResults);
        await FileSystem.WriteRecordsToCsvFile(
            Path.Combine(outputFolder, "Results.csv"), 
            raceResults.SelectMany(RaceResultRecord.ListFrom));
    }

    private (DateOnly start, DateOnly end, string outputFolder) ValidateOptions(DownloadResultsOptions options)
    {
        var (start, end)  = ValidateAndParseDateRange(options.DateRange);
        var outputFolder = ValidateAndCreateOutputFolder(options.OutputDirectory);
        return (start, end, outputFolder);
    }
}