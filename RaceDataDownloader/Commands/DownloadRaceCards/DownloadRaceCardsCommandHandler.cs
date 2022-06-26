using System.Globalization;
using System.IO.Abstractions;
using System.Net;
using CsvHelper;
using Microsoft.Extensions.Logging;
using RacePredictor.Core;
using RacePredictor.Core.RacingPost;
using ValidationException = System.ComponentModel.DataAnnotations.ValidationException;

namespace RaceDataDownloader.Commands.DownloadRaceCards;

public class DownloadRaceCardsCommandHandler : FileCommandHandlerBase
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly ILogger<DownloadRaceCardsCommandHandler> _logger;

    public DownloadRaceCardsCommandHandler(
        IFileSystem fileSystem,
        IHttpClientFactory httpClientFactory,
        ILogger<DownloadRaceCardsCommandHandler> logger) : base(fileSystem)
    {
        _httpClientFactory = httpClientFactory;
        _logger = logger;
    }

    public async Task<int> RunAsync(DownloadRaceCardsOptions options)
    {
        try
        {
            var (start, end, outputFolder) = ValidateOptions(options);
            var downloader = new RacingDataDownloader(_httpClientFactory);
            var raceResults = new List<RaceCard>();
            await foreach (var url in downloader.GetRaceCardUrls(start, end))
            {
                _logger.LogInformation("Attempting to load race card from {URL}", url);
                try
                {
                    var raceResult = await downloader.DownloadRaceCard(url);
                    raceResults.Add(raceResult);
                }
                catch (HttpRequestException hre)
                {
                    if (hre.StatusCode == HttpStatusCode.NotFound)
                    {
                        _logger.LogInformation("Skipping {URL} - could not find race card (404)", url);
                    }
                    else
                    {
                        throw;
                    }
                }
            }

            await SaveDataAsJson(Path.Combine(outputFolder, "RaceCards.json"), raceResults);
            await SaveResultsAsCsv(Path.Combine(outputFolder, "RaceCards.csv"), raceResults);
        }
        catch (ValidationException ve)
        {
            _logger.LogError(ve.Message);
            return ExitCodes.Error;
        }
        catch (Exception e)
        {
            _logger.LogError(e, "{Handler} failed with unexpected error", nameof(DownloadRaceCardsCommandHandler));
            return ExitCodes.Error;
        }

        return ExitCodes.Success;
    }

    private async Task SaveResultsAsCsv(string outputFileName, List<RaceCard> raceCards)
    {
        DeleteFileIfExists(outputFileName);

        await using var writer = new StringWriter();
        await using var csvWriter = new CsvWriter(writer, CultureInfo.InvariantCulture);

        await csvWriter.WriteRecordsAsync(
            raceCards
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
                    d.Race.Attributes.Going,
                    d.Race.Attributes.Surface,
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
                    d.Runner.Statistics.TopSpeedRating
                }));

        var csvString = writer.ToString();
        await FileSystem.File.WriteAllTextAsync(outputFileName, csvString);

    }

    private (DateOnly start, DateOnly end, string outputFolder) ValidateOptions(DownloadRaceCardsOptions options)
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