namespace RacePredictor.Core;

public class RaceOdds
{
    public RaceOdds(string fractionalOdds)
    {
        FractionalOdds = fractionalOdds;
        if (!string.IsNullOrEmpty(fractionalOdds))
        {
            if (fractionalOdds.ContainsAnyIgnoreCase("evens", "evs"))
            {
                DecimalOdds = 2.0;
                return;
            }

            if (fractionalOdds.Contains('/'))
            {
                var matches = @"(\d+)/(\d+)".GetMatches(fractionalOdds);
                var numerator = matches.Groups[1].Value.AsDouble();
                var denominator = matches.Groups[2].Value.AsDouble();
                DecimalOdds = (numerator / denominator) + 1;
            }
        }
    }

    public string FractionalOdds { get; }
    public double? DecimalOdds { get; }
}