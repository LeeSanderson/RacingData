namespace RacePredictor.Core;

// Per-runner "extras" captured forward-only from the racecard JSON island (Issue 005): first-time
// flags, trainer current form, jockey allowance, new-trainer count, country of origin and the raw
// Spotlight prose. Like Owner/Breeding these are JSON-only — null on the DOM-oracle reading, excluded
// from cross-validation — and NOT backfill-able (absent from result pages). Grouped as one value
// object so the new surface is cohesive rather than nine loose RaceRunner properties.
//
// Bool flags are nullable: null = the flag is absent from the card, false = present but not set,
// true = fired. WindSurgery and TrainerRtf are integers in the JSON (a wind-op indicator and a
// trainer current-form snapshot), captured faithfully rather than coerced to bools.
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
