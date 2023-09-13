using RaceDataDownloader.Commands.PredictTodaysRaceCards.Algorithms.RacingPostRating;

namespace RaceDataDownloader.Commands.PredictTodaysRaceCards.Algorithms;

public class RacePredictorFactory
{
    private readonly Dictionary<string, Func<IRacePredictor>> _predictors = new(StringComparer.InvariantCultureIgnoreCase);

    public RacePredictorFactory()
    {
        RegisterPredictor(nameof(RacingPostRatingPredictor), () => new RacingPostRatingPredictor());
    }

    public IRacePredictor GetPredictor(string algorithm) => _predictors[algorithm]();

    public void RegisterPredictor(string algorithm, Func<IRacePredictor> predictorGenerator) => _predictors[algorithm] = predictorGenerator;
}
