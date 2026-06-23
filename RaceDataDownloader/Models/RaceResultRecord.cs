using CsvHelper.Configuration.Attributes;
using RacePredictor.Core;

namespace RaceDataDownloader.Models;

public record RaceResultRecord : RaceRunnerRecord
{
    public static IEnumerable<RaceResultRecord> ListFrom(RaceResult raceResult) =>
        raceResult.Runners
            .Select(rnr => new { Race = raceResult, Runner = rnr })
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

    // Appended at the highest indices and [Optional] so results files written before these columns
    // still load. Unlike FractionalOdds/DecimalOdds (post-race SP), these hold the morning forecast.
    [Optional]
    [Index(40)]
    public string? ForecastFractionalOdds { get; set; }
    [Optional]
    [Index(41)]
    public double? ForecastDecimalOdds { get; set; }

    // Pre-race card fields, populated by the validate write-back rather than the result parser. [Optional]
    // so results files written before these columns still load.
    [Optional]
    [Index(42)]
    public int? DaysSinceLastRun { get; set; }
    [Optional]
    [Index(43)]
    public string? FormFigures { get; set; }
    [Optional]
    [Index(44)]
    public string? PrizeMoney { get; set; }
    [Optional]
    [Index(45)]
    public decimal? PrizeMoneyValue { get; set; }

    // Pre-race OR/RPR/TSR copied from the card by the write-back. The `Card` prefix distinguishes them
    // from the inherited post-race OfficialRating/RacingPostRating/TopSpeedRating: the Card* values are
    // non-leaky (known before the race) whereas the inherited ones are recomputed afterwards.
    [Optional]
    [Index(46)]
    public int? CardOfficialRating { get; set; }
    [Optional]
    [Index(47)]
    public int? CardRacingPostRating { get; set; }
    [Optional]
    [Index(48)]
    public int? CardTopSpeedRating { get; set; }

    // Owner, captured from the card and forwarded onto the result by the validate write-back. Forward-only,
    // so rows whose morning card no longer exists stay blank.
    [Optional]
    [Index(49)]
    public int? OwnerId { get; set; }
    [Optional]
    [Index(50)]
    public string? OwnerName { get; set; }

    // Breeding (sire/dam), captured from the card and forwarded onto the result by the validate write-back.
    // Forward-only, so rows whose morning card no longer exists stay blank.
    [Optional]
    [Index(51)]
    public string? SireName { get; set; }
    [Optional]
    [Index(52)]
    public string? SireCountry { get; set; }
    [Optional]
    [Index(53)]
    public string? DamName { get; set; }

    // Per-runner extras, captured from the card and forwarded onto the result by the validate write-back.
    // Forward-only, so rows whose morning card no longer exists stay blank. The three first-time flags carry
    // a captured false as false (the write-back gates on presence, not truthiness). WindSurgery and TrainerRtf
    // are integers in the JSON (a wind-op indicator and a trainer current-form snapshot), not bool flags.
    [Optional]
    [Index(54)]
    public bool? HeadgearFirstTime { get; set; }
    [Optional]
    [Index(55)]
    public bool? GeldingFirstTime { get; set; }
    [Optional]
    [Index(56)]
    public int? WindSurgery { get; set; }
    [Optional]
    [Index(57)]
    public int? TrainerRtf { get; set; }
    [Optional]
    [Index(58)]
    public int? JockeyAllowanceLbs { get; set; }
    [Optional]
    [Index(59)]
    public bool? JockeyFirstTime { get; set; }
    [Optional]
    [Index(60)]
    public int? NewTrainerRacesCount { get; set; }
    [Optional]
    [Index(61)]
    public string? CountryOfOrigin { get; set; }
    [Optional]
    [Index(62)]
    public string? Spotlight { get; set; }
}
