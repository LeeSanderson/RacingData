using RaceDataDownloader.Commands.PredictTodaysRaceCards;
using RaceDataDownloader.Models;

namespace RaceDataDownloader.Tests.Commands.PredictTodaysRaceCards;

public class RacingPostRatingPredictorShould
{
    private readonly List<RaceCardRecord> _raceCardForRaceBetweenHorse1AndHorse2 = new()
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

    private readonly List<RaceCardPrediction> _predictionThatHorse1WillWin = new()
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

        var generatedPredictions = predictor.PredictRaceCardResults(_raceCardForRaceBetweenHorse1AndHorse2);

        generatedPredictions.Should().BeEquivalentTo(_predictionThatHorse1WillWin);
    }
}