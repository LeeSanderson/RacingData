using RacePredictor.Core;

namespace RaceDataDownloader.Models;

public class RaceCardPredictionScore : RaceCardPrediction
{
    public int FinishingPosition { get; set; }
    public bool Won { get; set; }
    public string FractionalOdds { get; set; } = string.Empty;
    public double? DecimalOdds { get; set; }
    public ResultStatus ResultStatus { get; set; }
}