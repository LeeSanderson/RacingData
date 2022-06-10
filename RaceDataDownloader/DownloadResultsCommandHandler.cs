using System.Globalization;
using System.IO.Abstractions;
using System.Text.Json;
using System.Text.Json.Serialization;
using CsvHelper;
using Microsoft.Extensions.Logging;
using RacePredictor.Core;
using RacePredictor.Core.RacingPost;
using ValidationException = System.ComponentModel.DataAnnotations.ValidationException;

namespace RaceDataDownloader;

public class DownloadResultsCommandHandler
{
    private readonly IFileSystem _fileSystem;
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<DownloadResultsCommandHandler> _logger;

    public DownloadResultsCommandHandler(
        IFileSystem fileSystem,
        IHttpClientFactory httpClientFactory,
        ILogger<DownloadResultsCommandHandler> logger)
    {
        _fileSystem = fileSystem;
        _httpClientFactory = httpClientFactory;
        _logger = logger;
    }

    public async Task<int> RunAsync(DownloadResultsOptions options)
    {
        try
        {
            var (start, end, outputFolder) = ValidateOptions(options);
            var downloader = new RacingDataDownloader(_httpClientFactory);
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
            }

            await SaveResultsAsJson(Path.Combine(outputFolder, "Results.json"), raceResults);
            await SaveResultsAsCsv(Path.Combine(outputFolder, "Results.csv"), raceResults);
        }
        catch (ValidationException ve)
        {
            _logger.LogError(ve.Message);
            return 1;
        }
        catch (Exception e)
        {
            _logger.LogError(e, "{Handler} failed with unexpected error", nameof(DownloadResultsCommandHandler));
            return 1;
        }

        return 0;
    }

    private async Task SaveResultsAsCsv(string outputFileName, List<RaceResult> raceResults)
    {
        DeleteFileIfExists(outputFileName);

        await using var writer = new StringWriter();
        await using var csvWriter = new CsvWriter(writer, CultureInfo.InvariantCulture);
        
        await csvWriter.WriteRecordsAsync(
            raceResults
                .SelectMany(r => r.Runners.Select(rnr => new { Race = r, Runner = rnr }))
                .Select(d => new
                {
                    RaceId = d.Race.Race.Id,
                    RaceName = d.Race.Race.Name,
                    CourseId = d.Race.Course.Id,
                    CourseName = d.Race.Course.Name,
                    d.Race.Attributes.Classification,
                    d.Race.Attributes.Distance.Distance,
                    d.Race.Attributes.Distance.DistanceInFurlongs,
                    d.Race.Attributes.Distance.DistanceInMeters,
                    d.Race.Attributes.Distance.DistanceInYards,
                    HorseId = d.Runner.Horse.Id,
                    HorseName = d.Runner.Horse.Name,
                    JockeyId = d.Runner.Jockey.Id,
                    JockeyName = d.Runner.Jockey.Name,
                    TrainerId = d.Runner.Trainer.Id,
                    TrainerName = d.Runner.Trainer.Name,
                    d.Runner.Attributes.Age,
                    d.Runner.Attributes.HeadGear,
                    d.Runner.Attributes.RaceCardNumber,
                    d.Runner.Attributes.StallNumber,
                    Weight = d.Runner.Attributes.Weight.ToString(),
                    WeightInPounds = d.Runner.Attributes.Weight.TotalPounds,
                    d.Runner.Statistics.Odds.FractionalOdds,
                    d.Runner.Statistics.Odds.DecimalOdds,
                    d.Runner.Statistics.OfficialRating,
                    d.Runner.Statistics.RacingPostRating,
                    d.Runner.Statistics.TopSpeedRating,
                    d.Runner.Results.ResultStatus,
                    d.Runner.Results.FinishingPosition,
                    d.Runner.Results.BeatenDistance,
                    d.Runner.Results.OverallBeatenDistance,
                    d.Runner.Results.RaceTime,
                    d.Runner.Results.RaceTimeInSeconds
                }));

        var csvString = writer.ToString();
        await _fileSystem.File.WriteAllTextAsync(outputFileName, csvString);
    }

    private async Task SaveResultsAsJson(string outputFileName, List<RaceResult> raceResults)
    {
        DeleteFileIfExists(outputFileName);

        var jsonString = JsonSerializer.Serialize(raceResults,
            new JsonSerializerOptions
            {
                DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull, 
                IgnoreReadOnlyProperties = false,
                WriteIndented = true,
                Converters = { new JsonStringEnumConverter() }
            });

        await _fileSystem.File.WriteAllTextAsync(outputFileName, jsonString);
    }

    private void DeleteFileIfExists(string fileName)
    {
        if (_fileSystem.File.Exists(fileName))
        {
            _fileSystem.File.Delete(fileName);
            if (_fileSystem.File.Exists(fileName))
            {
                throw new ValidationException($"Unable to delete existing file {fileName}");
            }
        }
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

        if (!_fileSystem.Directory.Exists(outputFolder))
        {
            _fileSystem.Directory.CreateDirectory(outputFolder);
            if (!_fileSystem.Directory.Exists(outputFolder))
            {
                throw new ValidationException($"Unable to create 'output' directory '{outputFolder}' ");
            }
        }

        return (start, end, outputFolder);
    }
}