namespace RacePredictor.Core;

public class RaceResultRunnerResults
{
    public RaceResultRunnerResults(int finishingPosition, bool fell, double beatenDistance, double overallBeatenDistance,  TimeSpan raceTime)
    {
        FinishingPosition = finishingPosition;
        Fell = fell;
        OverallBeatenDistance = overallBeatenDistance;
        BeatenDistance = beatenDistance;
        RaceTime = raceTime;
    }

    public int FinishingPosition { get; }
    public bool Fell { get; }
    public double BeatenDistance { get; }
    public double OverallBeatenDistance { get; }
    public TimeSpan RaceTime { get; }
    public double RaceTimeInSeconds => RaceTime.TotalSeconds;
}