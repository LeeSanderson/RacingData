using RacePredictor.Core;

namespace RaceDataDownloader.Models;

public record RaceResultRecord
{
    public static IEnumerable<RaceResultRecord> ListFrom(RaceResult raceResult)
    {
        return raceResult.Runners
            .Select(rnr => new {Race = raceResult, Runner = rnr})
            .Select(d =>
                new RaceResultRecord
                {
                    RaceId = d.Race.Race.Id,
                    RaceName = d.Race.Race.Name,
                    CourseId = d.Race.Course.Id,
                    CourseName = d.Race.Course.Name,
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
    }

    public int RaceId { get; set; }
    public string RaceName { get; set; } = string.Empty;
    public int CourseId { get; set; }
    public string CourseName { get; set; } = string.Empty;
    public RaceType RaceType { get; set; }
    public string? Class { get; set; }
    public string? Pattern { get; set; }
    public string? RatingBand { get; set; }
    public string? AgeBand { get; set; }
    public RaceSexRestriction SexRestriction { get; set; }
    public string Distance { get; set; } = string.Empty;
    public double DistanceInFurlongs { get; set; }
    public int DistanceInMeters { get; set; }
    public int DistanceInYards { get; set; }
    public string? Going { get; set; }
    public RaceSurface Surface { get; set; }
    public int HorseId { get; set; }
    public string HorseName { get; set; } = string.Empty;
    public int JockeyId { get; set; }
    public string JockeyName { get; set; } = string.Empty;
    public int TrainerId { get; set; }
    public string TrainerName { get; set; } = string.Empty;
    public int Age { get; set; }
    public string? HeadGear { get; set; }
    public int RaceCardNumber { get; set; }
    public int? StallNumber { get; set; }
    public string Weight { get; set; } = string.Empty;
    public int WeightInPounds { get; set; }
    public string FractionalOdds { get; set; } = "SP";
    public double? DecimalOdds { get; set; }
    public int? OfficialRating { get; set; }
    public int? RacingPostRating { get; set; }
    public int? TopSpeedRating { get; set; }
    public ResultStatus ResultStatus { get; set; }
    public int FinishingPosition { get; set; }
    public double BeatenDistance { get; set; }
    public double OverallBeatenDistance { get; set; }
    public TimeSpan RaceTime { get; set; }
    public double RaceTimeInSeconds { get; set; }
}