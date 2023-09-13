using System.ComponentModel.DataAnnotations;
using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using RaceDataDownloader.Commands.PredictTodaysRaceCards.Algorithms;
using RaceDataDownloader.Models;

namespace RaceDataDownloader.Commands.PredictTodaysRaceCards;

public class PredictTodaysRaceCardsCommandHandler : FileCommandHandlerBase<PredictTodaysRaceCardsCommandHandler, PredictTodaysRaceCardsOptions>
{
    private readonly RacePredictorFactory _racePredictorFactory;

    public PredictTodaysRaceCardsCommandHandler(
        IFileSystem fileSystem,
        RacePredictorFactory racePredictorFactory,
        ILogger<PredictTodaysRaceCardsCommandHandler> logger) : base(fileSystem, logger)
    {
        _racePredictorFactory = racePredictorFactory;
    }

    protected override async Task InternalRunAsync(PredictTodaysRaceCardsOptions options)
    {
        var dataFolder = ValidateAndCreateOutputFolder(options.DataDirectory);
        var algorithm = options.Algorithm ?? throw new ValidationException("Required 'algorithm' parameter was not provided.");
        var raceCardsToPredict = await LoadRaceCardsToPredict(dataFolder);

        var predictor = _racePredictorFactory.GetPredictor(algorithm);
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
