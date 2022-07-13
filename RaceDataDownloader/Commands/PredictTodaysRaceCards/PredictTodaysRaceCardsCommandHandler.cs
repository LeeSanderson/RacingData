using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using RaceDataDownloader.Models;

namespace RaceDataDownloader.Commands.PredictTodaysRaceCards;

public class PredictTodaysRaceCardsCommandHandler : FileCommandHandlerBase<PredictTodaysRaceCardsCommandHandler, PredictTodaysRaceCardsOptions>
{
    public PredictTodaysRaceCardsCommandHandler(
        IFileSystem fileSystem,
        ILogger<PredictTodaysRaceCardsCommandHandler> logger) : base(fileSystem, logger)
    {
    }

    protected override async Task InternalRunAsync(PredictTodaysRaceCardsOptions options)
    {
        var dataFolder = ValidateAndCreateOutputFolder(options.DataDirectory);
        var raceCardsToPredict = await LoadRaceCardsToPredict(dataFolder);

        var predictor = new RacingPostRatingPredictor();
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
}