namespace RacePredictor.Core;

public class RaceResultRunnerStats
{
    public RaceResultRunnerStats(RaceOdds odds, int? officialRating, int? racingPostRating, int? topSpeedRating)
    {
        Odds = odds;
        OfficialRating = officialRating;
        RacingPostRating = racingPostRating;
        TopSpeedRating = topSpeedRating;
    }

    public RaceOdds Odds { get; }
    public int? OfficialRating { get; }
    public int? RacingPostRating { get; }
    public int? TopSpeedRating { get; }
}