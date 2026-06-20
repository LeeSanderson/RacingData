namespace RacePredictor.Core;

public class RaceRunnerAttributes
{
    public RaceRunnerAttributes(int raceCardNumber, int? stallNumber, int age, RaceWeight weight, string? headGear, int? daysSinceLastRun = null, string? formFigures = null)
    {
        RaceCardNumber = raceCardNumber;
        StallNumber = stallNumber;
        Age = age;
        Weight = weight;
        HeadGear = headGear;
        DaysSinceLastRun = daysSinceLastRun;
        FormFigures = formFigures;
    }

    public int RaceCardNumber { get; }
    public int? StallNumber { get;  }
    public int Age { get; }
    public RaceWeight Weight { get; }
    public string? HeadGear { get; }

    // Pre-race facts off the racecard runner row; null/empty for first-time runners.
    public int? DaysSinceLastRun { get; }
    public string? FormFigures { get; }

}