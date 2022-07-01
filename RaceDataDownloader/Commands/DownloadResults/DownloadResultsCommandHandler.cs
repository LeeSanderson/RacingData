using System.Globalization;
using System.IO.Abstractions;
using System.Net;
using CsvHelper;
using Microsoft.Extensions.Logging;
using RaceDataDownloader.Models;
using RacePredictor.Core;
using RacePredictor.Core.RacingPost;
using ValidationException = System.ComponentModel.DataAnnotations.ValidationException;

namespace RaceDataDownloader.Commands.DownloadResults;

public class DownloadResultsCommandHandler : FileCommandHandlerBase
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly IClock _clock;
    private readonly ILogger<DownloadResultsCommandHandler> _logger;

    public DownloadResultsCommandHandler(
        IFileSystem fileSystem,
        IHttpClientFactory httpClientFactory,
        IClock clock,
        ILogger<DownloadResultsCommandHandler> logger) : base(fileSystem)
    {
        _httpClientFactory = httpClientFactory;
        _clock = clock;
        _logger = logger;
    }

    public async Task<int> RunAsync(DownloadResultsOptions options)
    {
        try
        {
            var (start, end, outputFolder) = ValidateOptions(options);
            var downloader = new RacingDataDownloader(_httpClientFactory, _clock);
            var raceResults = new List<RaceResult>();
            await foreach (var url in downloader.GetResultUrls(start, end))
            {
                _logger.LogInformation("Attempting to load race results from {URL}", url);
                try
                {
                    var raceResult = await downloader.DownloadResults(url);
                    raceResults.Add(raceResult);
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

            await SaveDataAsJson(Path.Combine(outputFolder, "Results.json"), raceResults);
            await SaveResultsAsCsv(Path.Combine(outputFolder, "Results.csv"), raceResults);
        }
        catch (ValidationException ve)
        {
            _logger.LogError(ve.Message);
            return ExitCodes.Error;
        }
        catch (Exception e)
        {
            _logger.LogError(e, "{Handler} failed with unexpected error", nameof(DownloadResultsCommandHandler));
            return ExitCodes.Error;
        }

        return ExitCodes.Success;
    }

    private async Task SaveResultsAsCsv(string outputFileName, List<RaceResult> raceResults)
    {
        DeleteFileIfExists(outputFileName);

        await using var writer = new StringWriter();
        await using var csvWriter = new CsvWriter(writer, CultureInfo.InvariantCulture);

        await csvWriter.WriteRecordsAsync(raceResults.SelectMany(RaceResultRecord.ListFrom));

        var csvString = writer.ToString();
        await FileSystem.File.WriteAllTextAsync(outputFileName, csvString);
    }

    private (DateOnly start, DateOnly end, string outputFolder) ValidateOptions(DownloadResultsOptions options)
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

        CreateDirectoryIfNotExists(outputFolder);
        return (start, end, outputFolder);
    }
}