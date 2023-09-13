using RaceDataDownloader.Models;

namespace RaceDataDownloader.Commands.PredictTodaysRaceCards.Algorithms.RacingPostRating;

/// <summary>
/// A relatively naive prediction algorithm that predicts the winner based on the "Racing post rating"
/// While this seems highly accurate (based on historical race results data), actual race data is wildly inaccurate
/// (seems like the Racing Post update their rating after the race in order to seem more predictive)
/// </summary>
public class RacingPostRatingPredictor : IRacePredictor
{
    public IEnumerable<RaceCardPrediction> PredictRaceCardResults(List<RaceCardRecord> raceCardsToPredict)
    {
        var races = raceCardsToPredict.GroupBy(r => r.RaceId);
        foreach (var race in races)
        {
            RaceCardRecord? topRatedHorseRaceCardRecord = null;
            double topRating = 0;
            foreach (var runner in race)
            {
                var rating = runner.OfficialRating;
                if (rating != null && rating.Value > topRating)
                {
                    topRatedHorseRaceCardRecord = runner;
                    topRating = rating.Value;
                }
            }

            if (topRatedHorseRaceCardRecord != null)
            {
                yield return new RaceCardPrediction
                {
                    CourseId = topRatedHorseRaceCardRecord.CourseId,
                    CourseName = topRatedHorseRaceCardRecord.CourseName,
                    RaceId = topRatedHorseRaceCardRecord.RaceId,
                    RaceName = topRatedHorseRaceCardRecord.RaceName,
                    HorseId = topRatedHorseRaceCardRecord.HorseId,
                    HorseName = topRatedHorseRaceCardRecord.HorseName,
                    Off = topRatedHorseRaceCardRecord.Off
                };
            }
        }
    }
}
