namespace RacePredictor.Core;

public class RaceAttributes
{
    public RaceAttributes(DateTime off, RaceDistance distance, RaceClassification classification, string? going, int numberOfRunners)
    {
        Off = off;
        Distance = distance;
        Classification = classification;
        Going = going;
        NumberOfRunners = numberOfRunners;
    }

    public DateTime Off { get; }
    public RaceDistance Distance { get; }
    public RaceClassification Classification { get; }
    public string? Going { get; }
    public RaceSurface Surface => Going.ToRaceSurface();
    public int NumberOfRunners { get; }
}