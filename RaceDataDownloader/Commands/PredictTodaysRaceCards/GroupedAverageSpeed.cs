using RacePredictor.Core;

namespace RaceDataDownloader.Commands.PredictTodaysRaceCards;

public record GroupedAverageSpeed
{
    public int HorseId { get; set; }
    public RaceType RaceType { get; set; }
    public string Going { get; set; } = string.Empty;
    public DistanceType DistanceType { get; set; }
    public double AverageSpeed { get; set; }
}