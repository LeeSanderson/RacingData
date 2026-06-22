namespace RacePredictor.Core;

// Per-runner extras captured forward-only from the racecard JSON island; null on the DOM-oracle
// reading and excluded from cross-validation. Bool flags are nullable: null = absent from the card,
// false = present but not set, true = fired.
public class RaceRunnerExtras
{
    public RaceRunnerExtras(
        bool? headgearFirstTime,
        bool? geldingFirstTime,
        int? windSurgery,
        int? trainerRtf,
        int? jockeyAllowanceLbs,
        bool? jockeyFirstTime,
        int? newTrainerRacesCount,
        string? countryOfOrigin,
        string? spotlight)
    {
        HeadgearFirstTime = headgearFirstTime;
        GeldingFirstTime = geldingFirstTime;
        WindSurgery = windSurgery;
        TrainerRtf = trainerRtf;
        JockeyAllowanceLbs = jockeyAllowanceLbs;
        JockeyFirstTime = jockeyFirstTime;
        NewTrainerRacesCount = newTrainerRacesCount;
        CountryOfOrigin = countryOfOrigin;
        Spotlight = spotlight;
    }

    public bool? HeadgearFirstTime { get; }
    public bool? GeldingFirstTime { get; }
    public int? WindSurgery { get; }

    // A capture-time snapshot of the trainer's current-form rolling stat; a currency property knowable
    // pre-race, not leakage — frozen at capture, never reconstructed historically.
    public int? TrainerRtf { get; }

    public int? JockeyAllowanceLbs { get; }
    public bool? JockeyFirstTime { get; }
    public int? NewTrainerRacesCount { get; }
    public string? CountryOfOrigin { get; }

    // Raw analyst prose banked verbatim for a future NLP pipeline; no parsing or feature derivation.
    public string? Spotlight { get; }
}
