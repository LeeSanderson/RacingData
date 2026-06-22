namespace RacePredictor.Core;

// Breeding (sire name/country, dam name) is a forward-only racecard fact captured from the JSON
// island; it is absent from result pages, so it is null on the DOM-oracle reading and excluded from
// cross-validation. Grouped as a value object so the new surface is cohesive rather than three loose
// RaceRunner properties.
public class RaceRunnerBreeding
{
    public RaceRunnerBreeding(string? sireName, string? sireCountry, string? damName)
    {
        SireName = sireName;
        SireCountry = sireCountry;
        DamName = damName;
    }

    public string? SireName { get; }
    public string? SireCountry { get; }
    public string? DamName { get; }
}
