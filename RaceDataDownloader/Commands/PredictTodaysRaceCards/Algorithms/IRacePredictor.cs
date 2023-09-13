using RaceDataDownloader.Models;

namespace RaceDataDownloader.Commands.PredictTodaysRaceCards.Algorithms;

public interface IRacePredictor
{
    IEnumerable<RaceCardPrediction> PredictRaceCardResults(List<RaceCardRecord> raceCardsToPredict);
}
