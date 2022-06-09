namespace RacePredictor.Core;

/// <summary>
/// Distance in miles, furlongs, and yards e.g. "2m140yds"
/// </summary>
public class RaceDistance
{
    private const double NumberOfFurlongsInOneMile = 8.0;
    private const double NumberOfYardsInOneFurlong = 220.0;
    private const double NumberOfMetersInOneYard = 0.914;

    public RaceDistance(string distance) 
    {
        Distance = distance ?? throw new ArgumentNullException(nameof(distance));
        var cleanDistance = Distance.Replace("¼", ".25").Replace("½", ".5").Replace("¾", ".75");
        var milesPart = (@"(\d+)m".FindMatch(cleanDistance) ?? "0").AsInt();
        var furlongPart = (@"([\.\d]+)f".FindMatch(cleanDistance) ?? "0").AsDouble();
        var yardsPart = (@"([\.\d]+)yrds".FindMatch(cleanDistance) ?? "0").AsDouble();

        DistanceInFurlongs = milesPart * NumberOfFurlongsInOneMile + furlongPart;
        DistanceInYards = (int)(DistanceInFurlongs * NumberOfYardsInOneFurlong + yardsPart);
        DistanceInMeters = (int)(DistanceInYards * NumberOfMetersInOneYard);
    }

    public string Distance { get; }
    public double DistanceInFurlongs { get; }
    public int DistanceInMeters { get; }
    public int DistanceInYards { get; }
}