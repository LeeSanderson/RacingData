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

    // Appended at the highest indices and [Optional] so results files written before these columns
    // still load. Unlike FractionalOdds/DecimalOdds (post-race SP), these hold the morning forecast.
    [Optional]
    [Index(40)]
    public string? ForecastFractionalOdds { get; set; }
    [Optional]
    [Index(41)]
    public double? ForecastDecimalOdds { get; set; }

    // The base RaceCardRecord places these at indices 34-37 for the (daily-rewritten) card file, but
    // results already use 34-41 for post-race + forecast columns. Re-declare them with `new` so they
    // append after the forecast columns in the results layout. CsvHelper's auto-map binds the most-
    // derived property, so the hidden base index is ignored and no column is duplicated. [Optional]
    // so results files written before these columns still load. Populated by the validate write-back,
    // not the result parser — blank until then.
    [Optional]
    [Index(42)]
    public new int? DaysSinceLastRun { get; set; }
    [Optional]
    [Index(43)]
    public new string? FormFigures { get; set; }
    [Optional]
    [Index(44)]
    public new string? PrizeMoney { get; set; }
    [Optional]
    [Index(45)]
    public new decimal? PrizeMoneyValue { get; set; }

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

    // The base RaceCardRecord places owner at indices 38-39, which the results layout already uses for
    // RaceTime / RaceTimeInSeconds. Re-declare with `new` so owner appends at the end of the results
    // layout instead of colliding (same shadowing pattern as DaysSinceLastRun..PrizeMoneyValue above).
    // Owner is captured forward-only from the card and is not part of the card->result
    // write-back, so these stay blank in the results layout.
    [Optional]
    [Index(49)]
    public new int? OwnerId { get; set; }
    [Optional]
    [Index(50)]
    public new string? OwnerName { get; set; }

    // The base RaceCardRecord places breeding at indices 40-42, which the results layout already uses
    // for ForecastFractionalOdds / ForecastDecimalOdds / DaysSinceLastRun. Re-declare with `new` so
    // breeding appends at the end of the results layout instead of colliding (same shadowing pattern as
    // DaysSinceLastRun..PrizeMoneyValue and Owner above). Breeding is captured forward-only from the
    // card and is not part of the card->result write-back, so these stay blank in the results layout.
    [Optional]
    [Index(51)]
    public new string? SireName { get; set; }
    [Optional]
    [Index(52)]
    public new string? SireCountry { get; set; }
    [Optional]
    [Index(53)]
    public new string? DamName { get; set; }

    // The base RaceCardRecord places the per-runner extras at indices 43-51, which the results layout
    // already uses for FormFigures..SireName. Re-declare with `new` so they append at the end of the
    // results layout instead of colliding (same shadowing pattern as DaysSinceLastRun..DamName above).
    // Extras are captured forward-only from the card and are not part of the card->result write-back,
    // so these stay blank in the results layout.
    [Optional]
    [Index(54)]
    public new bool? HeadgearFirstTime { get; set; }
    [Optional]
    [Index(55)]
    public new bool? GeldingFirstTime { get; set; }
    [Optional]
    [Index(56)]
    public new int? WindSurgery { get; set; }
    [Optional]
    [Index(57)]
    public new int? TrainerRtf { get; set; }
    [Optional]
    [Index(58)]
    public new int? JockeyAllowanceLbs { get; set; }
    [Optional]
    [Index(59)]
    public new bool? JockeyFirstTime { get; set; }
    [Optional]
    [Index(60)]
    public new int? NewTrainerRacesCount { get; set; }
    [Optional]
    [Index(61)]
    public new string? CountryOfOrigin { get; set; }
    [Optional]
    [Index(62)]
    public new string? Spotlight { get; set; }
}
