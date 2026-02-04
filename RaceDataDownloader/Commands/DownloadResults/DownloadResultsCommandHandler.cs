using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using RaceDataDownloader.Models;
using RacePredictor.Core.RacingPost;

namespace RaceDataDownloader.Commands.DownloadResults;

public class DownloadResultsCommandHandler(
    IFileSystem fileSystem,
    IRacingDataDownloader downloader,
    ILogger<DownloadResultsCommandHandler> logger)
    : FileCommandHandlerBase<DownloadResultsCommandHandler, DownloadResultsOptions>(fileSystem, logger)
{
    protected override async Task InternalRunAsync(DownloadResultsOptions options)
    {
        var (start, end, outputFolder) = ValidateOptions(options);
        var raceResults = await downloader.DownloadRaceResultsInRange(Logger, start, end);

        await FileSystem.WriteRecordsToJsonFile(Path.Combine(outputFolder, "Results.json"), raceResults);
        await FileSystem.WriteRecordsToCsvFile(
            Path.Combine(outputFolder, "Results.csv"),
            raceResults.SelectMany(RaceResultRecord.ListFrom));
    }

    private (DateOnly start, DateOnly end, string outputFolder) ValidateOptions(DownloadResultsOptions options)
    {
        var (start, end) = ValidateAndParseDateRange(options.DateRange);
        var outputFolder = ValidateAndCreateOutputFolder(options.OutputDirectory);
        return (start, end, outputFolder);
    }
}
