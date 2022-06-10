using System.ComponentModel.DataAnnotations;
using System.IO.Abstractions;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.Logging;
using RacePredictor.Core;
using RacePredictor.Core.RacingPost;

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

    private async Task SaveResultsAsJson(string outputFileName, List<RaceResult> raceResults)
    {
        if (_fileSystem.File.Exists(outputFileName))
        {
            _fileSystem.File.Delete(outputFileName);
            if (_fileSystem.File.Exists(outputFileName))
            {
                throw new ValidationException($"Unable to delete existing output file {outputFileName}");
            }
        }

        var jsonString = JsonSerializer.Serialize(raceResults,
            new JsonSerializerOptions
            {
                DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingDefault, 
                IgnoreReadOnlyProperties = false,
                WriteIndented = true,
                Converters = { new JsonStringEnumConverter() }
            });

        await _fileSystem.File.WriteAllTextAsync(outputFileName, jsonString);
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