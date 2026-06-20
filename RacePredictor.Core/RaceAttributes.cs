namespace RacePredictor.Core;

public class RaceAttributes
{
    public RaceAttributes(DateTime off, RaceDistance distance, RaceClassification classification, string? going, int numberOfRunners, string? prizeMoney = null, decimal? prizeMoneyValue = null)
    {
        Off = off;
        Distance = distance;
        Classification = classification;
        Going = going;
        NumberOfRunners = numberOfRunners;
        PrizeMoney = prizeMoney;
        PrizeMoneyValue = prizeMoneyValue;
    }

    public DateTime Off { get; }
    public RaceDistance Distance { get; }
    public RaceClassification Classification { get; }
    public string? Going { get; }
    public RaceSurface Surface => Going.ToRaceSurface();
    public int NumberOfRunners { get; }

    // Raw display string (currency symbol + thousands separators preserved); currency is NOT
    // normalised across countries. PrizeMoneyValue is the same figure with symbol/commas stripped.
    public string? PrizeMoney { get; }
    public decimal? PrizeMoneyValue { get; }
}