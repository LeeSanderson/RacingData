using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using RaceDataDownloader.Models;
using RacePredictor.Core.RacingPost;

namespace RaceDataDownloader.Commands.UpdateResults;

public class UpdateResultsCommandHandler(
    IFileSystem fileSystem,
    IRacingDataDownloader downloader,
    IClock clock,
    ILogger<UpdateResultsCommandHandler> logger)
    : FileCommandHandlerBase<UpdateResultsCommandHandler, UpdateResultsOptions>(fileSystem, logger)
{
    protected override async Task InternalRunAsync(UpdateResultsOptions options)
    {
        var (start, end, dataFolder) = ValidateOptions(options);
        foreach (var (monthStart, monthEnd) in DateRange.SplitRangeIntoMonths(start, end))
        {
            await UpdateMonthlyResultsFile(monthStart, monthEnd, dataFolder);
        }
    }

    private async Task UpdateMonthlyResultsFile(DateOnly monthStart, DateOnly monthEnd, string dataFolder)
    {
        var monthlyResultsFile = FileSystem.GetResultsFileName(dataFolder, monthStart);
        List<RaceResultRecord> raceResults;
        if (FileSystem.File.Exists(monthlyResultsFile))
        {
            raceResults = await FileSystem.ReadRecordsFromCsvFile<RaceResultRecord>(monthlyResultsFile);
            var maxOffDate = DateOnly.FromDateTime(raceResults.Max(x => x.Off));
            var minOffDate = DateOnly.FromDateTime(raceResults.Min(x => x.Off));
            if (monthStart >= minOffDate && monthEnd <= maxOffDate)
            {
                Logger.LogInformation("Skipping update for {FileName} - file contains data for entire period.", monthlyResultsFile);
                return;
            }

            if (monthStart < minOffDate)
            {
                var preCurrentRaceResults = await GetRaceResultRecordsInRange(monthStart, minOffDate.AddDays(-1));
                raceResults.AddRange(preCurrentRaceResults);
            }

            if (monthEnd > maxOffDate)
            {
                var postCurrentRaceResults = await GetRaceResultRecordsInRange(maxOffDate.AddDays(1), monthEnd);
                raceResults.AddRange(postCurrentRaceResults);
            }
        }
        else
        {
            raceResults = await GetRaceResultRecordsInRange(monthStart, monthEnd);
        }

        await FileSystem.WriteRecordsToCsvFile(monthlyResultsFile, raceResults);
    }

    private async Task<List<RaceResultRecord>> GetRaceResultRecordsInRange(DateOnly monthStart, DateOnly monthEnd)
    {
        Logger.LogInformation("Updating file with data for period {Start} to {End}.", monthStart, monthEnd);
        var raceResults = await downloader.DownloadRaceResultsInRange(Logger, monthStart, monthEnd);
        return raceResults.SelectMany(RaceResultRecord.ListFrom).ToList();
    }

    private (DateOnly start, DateOnly end, string dataFolder) ValidateOptions(UpdateResultsOptions options)
    {
        var dataFolder = ValidateAndCreateOutputFolder(options.DataDirectory);

        var range = options.MinimumPeriodInDays < 1 ? DefaultOptions.MinimumPeriodInDays : options.MinimumPeriodInDays;
        var start = clock.Today.AddDays(-range);
        var end = clock.Today.AddDays(-1);

        return (start, end, dataFolder);
    }
}
