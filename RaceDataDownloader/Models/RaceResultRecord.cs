using CsvHelper.Configuration.Attributes;
using RacePredictor.Core;

namespace RaceDataDownloader.Models;

public record RaceResultRecord : RaceCardRecord
{
    public static IEnumerable<RaceResultRecord> ListFrom(RaceResult raceResult) =>
        raceResult.Runners
            .Select(rnr => new {Race = raceResult, Runner = rnr})
            .Select(d =>
                new RaceResultRecord
                {
                    RaceId = d.Race.Race.Id,
                    RaceName = d.Race.Race.Name,
                    CourseId = d.Race.Course.Id,
                    CourseName = d.Race.Course.Name,
                    Off = d.Race.Attributes.Off,
                    RaceType = d.Race.Attributes.Classification.RaceType,
                    Class = d.Race.Attributes.Classification.Class,
                    Pattern = d.Race.Attributes.Classification.Pattern,
                    RatingBand = d.Race.Attributes.Classification.RatingBand,
                    AgeBand = d.Race.Attributes.Classification.AgeBand,
                    SexRestriction = d.Race.Attributes.Classification.SexRestriction,
                    Distance = d.Race.Attributes.Distance.Distance,
                    DistanceInFurlongs = d.Race.Attributes.Distance.DistanceInFurlongs,
                    DistanceInMeters = d.Race.Attributes.Distance.DistanceInMeters,
                    DistanceInYards = d.Race.Attributes.Distance.DistanceInYards,
                    Going = d.Race.Attributes.Going,
                    Surface = d.Race.Attributes.Surface,
                    HorseId = d.Runner.Horse.Id,
                    HorseName = d.Runner.Horse.Name,
                    JockeyId = d.Runner.Jockey.Id,
                    JockeyName = d.Runner.Jockey.Name,
                    TrainerId = d.Runner.Trainer.Id,
                    TrainerName = d.Runner.Trainer.Name,
                    Age = d.Runner.Attributes.Age,
                    HeadGear = d.Runner.Attributes.HeadGear,
                    RaceCardNumber = d.Runner.Attributes.RaceCardNumber,
                    StallNumber = d.Runner.Attributes.StallNumber,
                    Weight = d.Runner.Attributes.Weight.ToString(),
                    WeightInPounds = d.Runner.Attributes.Weight.TotalPounds,
                    FractionalOdds = d.Runner.Statistics.Odds.FractionalOdds,
                    DecimalOdds = d.Runner.Statistics.Odds.DecimalOdds,
                    OfficialRating = d.Runner.Statistics.OfficialRating,
                    RacingPostRating = d.Runner.Statistics.RacingPostRating,
                    TopSpeedRating = d.Runner.Statistics.TopSpeedRating,
                    ResultStatus = d.Runner.Results.ResultStatus,
                    FinishingPosition = d.Runner.Results.FinishingPosition,
                    BeatenDistance = d.Runner.Results.BeatenDistance,
                    OverallBeatenDistance = d.Runner.Results.OverallBeatenDistance,
                    RaceTime = d.Runner.Results.RaceTime,
                    RaceTimeInSeconds = d.Runner.Results.RaceTimeInSeconds
                });

    [Index(34)]
    public ResultStatus ResultStatus { get; set; }
    [Index(35)]
    public int FinishingPosition { get; set; }
    [Index(36)]
    public double BeatenDistance { get; set; }
    [Index(37)]
    public double OverallBeatenDistance { get; set; }
    [Index(38)]
    public TimeSpan RaceTime { get; set; }
    [Index(39)]
    public double RaceTimeInSeconds { get; set; }
}
