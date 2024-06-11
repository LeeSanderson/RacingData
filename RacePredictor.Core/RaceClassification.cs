namespace RacePredictor.Core;

public class RaceClassification
{
    public RaceClassification(RaceType raceType, string? @class, string? pattern, string? ratingBand, string? ageBand, RaceSexRestriction sexRestriction)
    {
        RaceType = raceType;
        Class = @class;
        Pattern = pattern;
        RatingBand = ratingBand;
        AgeBand = ageBand;
        SexRestriction = sexRestriction;
    }

    public RaceType RaceType { get; }

    /// <summary>
    /// Class of the race indicating the quality of the runners
    /// See https://news.paddypower.com/guides/2022/02/01/class-horse-race-classes-paddy-power-betting-guide-flat/
    /// </summary>
    public string? Class { get; }

    /// <summary>
    /// Further division of the quality of the runners. The grade or group of a "Class 1" race 
    /// https://www.horseracingqa.com/what-is-a-pattern-race/
    /// </summary>
    public string? Pattern { get; }

    /// <summary>
    /// Related to <see cref="Class"/>. The band of official ratings of the runners (e.g. "0-145")
    /// </summary>
    public string? RatingBand { get; }

    /// <summary>
    /// The band of ages for the runners (e.g. "4yo+")
    /// </summary>
    public string? AgeBand { get; }

    /// <summary>
    /// Is the race restricted to runners of a particular sex (eg. "Colts and Fillies", "Mares", "Mares and Geldings" etc.)
    /// </summary>
    public RaceSexRestriction SexRestriction { get; }
}