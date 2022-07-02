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
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly IClock _clock;
    private readonly ILogger<UpdateResultsCommandHandler> _logger;

    public UpdateResultsCommandHandler(
        IFileSystem fileSystem,
        IHttpClientFactory httpClientFactory,
        IClock clock,
        ILogger<UpdateResultsCommandHandler> logger) : base(fileSystem)
    {
        _httpClientFactory = httpClientFactory;
        _clock = clock;
        _logger = logger;
    }

    public async Task<int> RunAsync(UpdateResultsOptions options)
    {
        try
        {

            var (start, end, dataFolder) = ValidateOptions(options);
            var downloader = new RacingDataDownloader(_httpClientFactory, _clock);
            var raceResults = new List<RaceResultRecord>();
            await foreach (var url in downloader.GetResultUrls(start, end))
            {
                _logger.LogInformation("Attempting to load race results from {URL}", url);
                try
                {
                    var raceResult = await downloader.DownloadResults(url);
                    raceResults.AddRange(RaceResultRecord.ListFrom(raceResult));
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

            await FileSystem.WriteRecordsToCsvFile(Path.Combine(dataFolder, $"Results_{start.Year}{start.Month:00}.csv"), raceResults);
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