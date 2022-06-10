using System.ComponentModel.DataAnnotations;
using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
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
            throw new NotImplementedException();
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