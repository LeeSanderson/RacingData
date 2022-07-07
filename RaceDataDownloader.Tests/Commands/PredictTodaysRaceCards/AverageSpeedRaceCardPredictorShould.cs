using RaceDataDownloader.Commands.PredictTodaysRaceCards;
using RaceDataDownloader.Models;
using RacePredictor.Core;

namespace RaceDataDownloader.Tests.Commands.PredictTodaysRaceCards;

public class AverageSpeedRaceCardPredictorShould
{
    private readonly List<RaceResultRecord> _resultsWhereHorse1IsFasterThanHorse2 = new()
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
    public void PredictHorse1WillWinWhenHorse1IsFasterThanHorse2()
    {
        var  predictor = new AverageSpeedRaceCardPredictor(_resultsWhereHorse1IsFasterThanHorse2);

        var generatedPredictions = predictor.PredictRaceCardResults(_raceCardForRaceBetweenHorse1AndHorse2);

        generatedPredictions.Should().BeEquivalentTo(_predictionThatHorse1WillWin);
    }
}