namespace RacePredictor.Core;

public class RaceResultRunnerResults
{
    public RaceResultRunnerResults(int finishingPosition, double beatenDistance, double overallBeatenDistance,  TimeSpan raceTime)
    {
        FinishingPosition = finishingPosition;
        OverallBeatenDistance = overallBeatenDistance;
        BeatenDistance = beatenDistance;
        RaceTime = raceTime;
    }

    public int FinishingPosition { get; }
    public double BeatenDistance { get; }
    public double OverallBeatenDistance { get; }
    public TimeSpan RaceTime { get; }
    public double RaceTimeInSeconds => RaceTime.TotalSeconds;
}