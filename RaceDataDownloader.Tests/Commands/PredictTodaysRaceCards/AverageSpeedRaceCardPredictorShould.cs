using RaceDataDownloader.Commands.PredictTodaysRaceCards;
using RaceDataDownloader.Models;
using RacePredictor.Core;

namespace RaceDataDownloader.Tests.Commands.PredictTodaysRaceCards;

public class AverageSpeedRaceCardPredictorShould
{
    private static readonly List<RaceResultRecord> ResultsWhereHorse1IsFasterThanHorse2 = new()
    {
        new RaceResultRecord
        {
            HorseId = 1,
            Off = new DateTime(2022, 05, 12, 13, 40, 0),
            RaceType = RaceType.Flat,
            DistanceInMeters = 3500,
            Going = "Good",
            RaceTimeInSeconds = 247.9
        },
        new RaceResultRecord
        {
            HorseId = 2,
            Off = new DateTime(2022, 05, 12, 13, 40, 0),
            RaceType = RaceType.Flat,
            DistanceInMeters = 3500,
            Going = "Good",
            RaceTimeInSeconds = 300.9
        }
    };

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
            RaceType = RaceType.Flat,
            DistanceInMeters = 3500,
            Going = "Good"
        },
        new RaceCardRecord
        {
            RaceId = 1,
            RaceName = "Race1",
            CourseId = 1,
            CourseName = "Course1",
            HorseId = 2,
            HorseName = "Horse2",
            RaceType = RaceType.Flat,
            DistanceInMeters = 3500,
            Going = "Good"
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
    public void PredictHorse1WillWinWhenHorse1IsFasterThanHorse2()
    {
        var predictor = new AverageSpeedRaceCardPredictor(ResultsWhereHorse1IsFasterThanHorse2);

        var generatedPredictions = predictor.PredictRaceCardResults(RaceCardForRaceBetweenHorse1AndHorse2);

        generatedPredictions.Should().BeEquivalentTo(PredictionThatHorse1WillWin);
    }
}
