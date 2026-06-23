using CsvHelper.Configuration.Attributes;
using RacePredictor.Core;

namespace RaceDataDownloader.Models;

// The columns RaceCardRecord and RaceResultRecord genuinely share, at CSV indices 0-33: race identity,
// classification, distance, going/surface, runner identity, runner attributes, and the pre-race stats
// block (forecast odds and pre-race OR/RPR/TSR).
public abstract record RaceRunnerRecord
{
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
