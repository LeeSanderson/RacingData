using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using RaceDataDownloader.Models;
using RacePredictor.Core.RacingPost;

namespace RaceDataDownloader.Commands.UpdateResults;

public class UpdateResultsCommandHandler : FileCommandHandlerBase<UpdateResultsCommandHandler, UpdateResultsOptions>
{
    private readonly IClock _clock;
    private readonly RacingDataDownloader _downloader;

    public UpdateResultsCommandHandler(
        IFileSystem fileSystem,
        IHttpClientFactory httpClientFactory,
        IClock clock,
        ILogger<UpdateResultsCommandHandler> logger) : base(fileSystem, logger)
    {
        _clock = clock;
        _downloader = new RacingDataDownloader(httpClientFactory, _clock);
    }

    protected override async Task InternalRunAsync(UpdateResultsOptions options)
    {
        var (start, end, dataFolder) = ValidateOptions(options);
        foreach (var (monthStart, monthEnd) in SplitRangeIntoMonths(start, end))
        {
            await UpdateMonthlyResultsFile(monthStart, monthEnd, dataFolder);
        }
    }

    private async Task UpdateMonthlyResultsFile(DateOnly monthStart, DateOnly monthEnd, string dataFolder)
    {
        var monthlyResultsFile = Path.Combine(dataFolder, $"Results_{monthStart.Year}{monthStart.Month:00}.csv");
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
                var preCurrentRaceResults = await GetRaceResultRecordsInRange(monthStart, monthEnd.AddDays(-1));
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
        var raceResults = await _downloader.DownloadRaceResultsInRange(Logger, monthStart, monthEnd);
        return raceResults.SelectMany(RaceResultRecord.ListFrom).ToList();
    }

    private static IEnumerable<(DateOnly monthStart, DateOnly monthEnd)> SplitRangeIntoMonths(DateOnly start, DateOnly end)
    {
        var monthStart = start;
        while (monthStart <= end)
        {
            var monthEnd = new DateOnly(monthStart.Year, monthStart.Month, DateTime.DaysInMonth(monthStart.Year, monthStart.Month));
            monthEnd = monthEnd > end ? end : monthEnd;
            yield return (monthStart, monthEnd);
            monthStart = monthEnd.AddDays(1);
        }
    }

    private (DateOnly start, DateOnly end, string dataFolder) ValidateOptions(UpdateResultsOptions options)
    {
        var dataFolder = ValidateAndCreateOutputFolder(options.DataDirectory);

        var range = options.MinimumPeriodInDays < 1 ? UpdateResultsOptions.DefaultMinimumPeriodInDays : options.MinimumPeriodInDays;
        var start = _clock.Today.AddDays(-range);
        var end = _clock.Today.AddDays(-1);

        return (start, end, dataFolder);
    }
}