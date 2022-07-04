using System.IO.Abstractions;
using System.Net;
using Microsoft.Extensions.Logging;
using RaceDataDownloader.Models;
using RacePredictor.Core;
using RacePredictor.Core.RacingPost;
using ValidationException = System.ComponentModel.DataAnnotations.ValidationException;

namespace RaceDataDownloader.Commands.UpdateResults;

public class UpdateResultsCommandHandler : FileCommandHandlerBase
{
    private readonly IClock _clock;
    private readonly ILogger<UpdateResultsCommandHandler> _logger;
    private readonly RacingDataDownloader _downloader;

    public UpdateResultsCommandHandler(
        IFileSystem fileSystem,
        IHttpClientFactory httpClientFactory,
        IClock clock,
        ILogger<UpdateResultsCommandHandler> logger) : base(fileSystem)
    {
        _clock = clock;
        _logger = logger;
        _downloader = new RacingDataDownloader(httpClientFactory, _clock);
    }

    public async Task<int> RunAsync(UpdateResultsOptions options)
    {
        try
        {
            var (start, end, dataFolder) = ValidateOptions(options);
            foreach (var (monthStart, monthEnd) in SplitRangeIntoMonths(start, end))
            {
                await UpdateMonthlyResultsFile(monthStart, monthEnd, dataFolder);
            }
        }
        catch (ValidationException ve)
        {
            _logger.LogError(ve.Message);
            return ExitCodes.Error;
        }
        catch (Exception e)
        {
            _logger.LogError(e, "{Handler} failed with unexpected error", nameof(UpdateResultsCommandHandler));
            return ExitCodes.Error;
        }

        return ExitCodes.Success;
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
        var raceResultRecords = new List<RaceResultRecord>();
        await foreach (var url in _downloader.GetResultUrls(monthStart, monthEnd))
        {
            _logger.LogInformation("Attempting to load race results from {URL}", url);
            try
            {
                var raceResult = await _downloader.DownloadResults(url);
                raceResultRecords.AddRange(RaceResultRecord.ListFrom(raceResult));
            }
            catch (VoidRaceException)
            {
                _logger.LogInformation("Skipping void race {URL}", url);
            }
            catch (HttpRequestException hre)
            {
                if (hre.StatusCode == HttpStatusCode.NotFound)
                {
                    _logger.LogInformation("Skipping {URL} - could not find race (404)", url);
                }
                else
                {
                    throw;
                }
            }
        }

        return raceResultRecords;
    }

    private IEnumerable<(DateOnly monthStart, DateOnly monthEnd)> SplitRangeIntoMonths(DateOnly start, DateOnly end)
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
        var dataFolder = options.DataDirectory ?? throw new ValidationException("Required 'output' parameter was not provided.");
        var range = options.MinimumPeriodInDays < 1 ? UpdateResultsOptions.DefaultMinimumPeriodInDays : options.MinimumPeriodInDays;
        var start = _clock.Today.AddDays(-range);
        var end = _clock.Today.AddDays(-1);

        FileSystem.CreateDirectoryIfNotExists(dataFolder);
        return (start, end, dataFolder);
    }
}