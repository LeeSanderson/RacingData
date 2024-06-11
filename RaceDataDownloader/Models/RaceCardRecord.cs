using CsvHelper.Configuration.Attributes;
using RacePredictor.Core;

namespace RaceDataDownloader.Models;

public record RaceCardRecord
{
    public static IEnumerable<RaceCardRecord> ListFrom(RaceCard raceCard) =>
        raceCard.Runners
            .Select(rnr => new { Race = raceCard, Runner = rnr })
            .Select(d => new RaceCardRecord
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
                TopSpeedRating = d.Runner.Statistics.TopSpeedRating
            });

    [Index(0)]
    public int RaceId { get; set; }
    [Index(1)]
    public string RaceName { get; set; } = string.Empty;
    [Index(2)]
    public int CourseId { get; set; }
    [Index(3)]
    public string CourseName { get; set; } = string.Empty;
    [Index(4)]
    public DateTime Off { get; set; }
    [Index(5)]
    public RaceType RaceType { get; set; }
    [Index(6)]
    public string? Class { get; set; }
    [Index(7)]
    public string? Pattern { get; set; }
    [Index(8)]
    public string? RatingBand { get; set; }
    [Index(9)]
    public string? AgeBand { get; set; }
    [Index(10)]
    public RaceSexRestriction SexRestriction { get; set; }
    [Index(11)]
    public string Distance { get; set; } = string.Empty;
    [Index(12)]
    public double DistanceInFurlongs { get; set; }
    [Index(13)]
    public int DistanceInMeters { get; set; }
    [Index(14)]
    public int DistanceInYards { get; set; }
    [Index(15)]
    public string? Going { get; set; }
    [Index(16)]
    public RaceSurface Surface { get; set; }
    [Index(17)]
    public int HorseId { get; set; }
    [Index(18)]
    public string HorseName { get; set; } = string.Empty;
    [Index(19)]
    public int JockeyId { get; set; }
    [Index(20)]
    public string JockeyName { get; set; } = string.Empty;
    [Index(21)]
    public int TrainerId { get; set; }
    [Index(22)]
    public string TrainerName { get; set; } = string.Empty;
    [Index(23)]
    public int Age { get; set; }
    [Index(24)]
    public string? HeadGear { get; set; }
    [Index(25)]
    public int RaceCardNumber { get; set; }
    [Index(26)]
    public int? StallNumber { get; set; }
    [Index(27)]
    public string Weight { get; set; } = string.Empty;
    [Index(28)]
    public int WeightInPounds { get; set; }
    [Index(29)]
    public string FractionalOdds { get; set; } = "SP";
    [Index(30)]
    public double? DecimalOdds { get; set; }
    [Index(31)]
    public int? OfficialRating { get; set; }
    [Index(32)]
    public int? RacingPostRating { get; set; }
    [Index(33)]
    public int? TopSpeedRating { get; set; }
}
