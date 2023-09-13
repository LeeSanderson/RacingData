using RaceDataDownloader.Commands.PredictTodaysRaceCards.Algorithms.RacingPostRating;
using RaceDataDownloader.Models;

namespace RaceDataDownloader.Tests.Commands.PredictTodaysRaceCards.Algorithms.RacingPostRating;

public class RacingPostRatingPredictorShould
{
    private static readonly List<RaceCardRecord> RaceCardForRaceBetweenHorse1AndHorse2 = new()
    {
        new RaceCardRecord
        {
            RaceId = 1,
            RaceName = "Race1",
            CourseId = 1,
            CourseName = "Course1",
            HorseId = 1,
            HorseName = "Horse1",
            Off = new DateTime(2022, 05, 13, 13, 40, 0),
            RacingPostRating = 100
        },
        new RaceCardRecord
        {
            RaceId = 1,
            RaceName = "Race1",
            CourseId = 1,
            CourseName = "Course1",
            HorseId = 2,
            HorseName = "Horse2",
            RacingPostRating = 99

        }
    };

    private static readonly List<RaceCardPrediction> PredictionThatHorse1WillWin = new()
    {
        new RaceCardPrediction
        {
            RaceId = 1,
            RaceName = "Race1",
            CourseId = 1,
            CourseName = "Course1",
            HorseId = 1,
            HorseName = "Horse1",
            Off = new DateTime(2022, 05, 13, 13, 40, 0),
        }
    };


    [Fact]
    public void PredictHorse1WillWinWhenHorse1RatingIsBetterThanHorse2()
    {
        var predictor = new RacingPostRatingPredictor();

        var generatedPredictions = predictor.PredictRaceCardResults(RaceCardForRaceBetweenHorse1AndHorse2);

        generatedPredictions.Should().BeEquivalentTo(PredictionThatHorse1WillWin);
    }
}
