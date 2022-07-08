using System.ComponentModel.DataAnnotations;
using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using RaceDataDownloader.Models;
using RacePredictor.Core.RacingPost;

namespace RaceDataDownloader.Commands.PredictTodaysRaceCards;

public class PredictTodaysRaceCardsCommandHandler : FileCommandHandlerBase<PredictTodaysRaceCardsCommandHandler, PredictTodaysRaceCardsOptions>
{
    private readonly IClock _clock;

    public PredictTodaysRaceCardsCommandHandler(
        IFileSystem fileSystem,
        IClock clock,
        ILogger<PredictTodaysRaceCardsCommandHandler> logger) : base(fileSystem, logger)
    {
        _clock = clock;
    }

    protected override async Task InternalRunAsync(PredictTodaysRaceCardsOptions options)
    {
        var (start, end, dataFolder) = ValidateOptions(options);
        var raceCardsToPredict = await LoadRaceCardsToPredict(dataFolder); 
        var historicResults = await LoadHistoricResultsInRange(dataFolder, start, end);
        
        var predictor = new AverageSpeedRaceCardPredictor(historicResults);
        var predictions = predictor.PredictRaceCardResults(raceCardsToPredict).ToList();
        Logger.LogInformation("Predicted winners for {PredictionCount} race cards", predictions.Count);

        await FileSystem.WriteRecordsToJsonFile(Path.Combine(dataFolder, "Predictions.json"), predictions);
    }

    private async Task<List<RaceCardRecord>> LoadRaceCardsToPredict(string dataFolder)
    {
        var raceCardRecords = await FileSystem.ReadRecordsFromCsvFile<RaceCardRecord>(Path.Combine(dataFolder, "TodaysRaceCards.csv"));
        var raceCardCount = raceCardRecords.Select(r => r.RaceId).Distinct().Count();
        Logger.LogInformation("Predicting results for {RaceCardCount} race cards", raceCardCount);
        return raceCardRecords;
    }

    private async Task<List<RaceResultRecord>> LoadHistoricResultsInRange(string dataFolder, DateOnly rangeStart, DateOnly rangeEnd)
    {
        var raceResults = new List<RaceResultRecord>();
        foreach (var (monthStart, _) in DateRange.SplitRangeIntoMonths(rangeStart, rangeEnd))
        {
            var monthlyResultsFile = FileSystem.GetResultsFileName(dataFolder, monthStart);
            if (FileSystem.File.Exists(monthlyResultsFile))
            {
                raceResults.AddRange(await FileSystem.ReadRecordsFromCsvFile<RaceResultRecord>(monthlyResultsFile));
            }
            else
            {
                Logger.LogWarning("Unable to find results file for {FileName} - predictions may be off", monthlyResultsFile);
            }
        }

        raceResults.RemoveAll(x => DateOnly.FromDateTime(x.Off) < rangeStart);
        if (raceResults.Count == 0)
        {
            throw new ValidationException("Unable to predict race cards - no historic data found");
        }

        var raceCount = raceResults.Select(r => r.RaceId).Distinct().Count();
        Logger.LogInformation("Using {RaceCount} historic races to predict race cards", raceCount);
        return raceResults;
    }

    private (DateOnly start, DateOnly end, string dataFolder) ValidateOptions(PredictTodaysRaceCardsOptions options)
    {
        var dataFolder = ValidateAndCreateOutputFolder(options.DataDirectory);

        var range = options.HistoricPeriodInDays < 1 ? DefaultOptions.MinimumPeriodInDays : options.HistoricPeriodInDays;
        var start = _clock.Today.AddDays(-range);
        var end = _clock.Today.AddDays(-1);

        return (start, end, dataFolder);
    }
}