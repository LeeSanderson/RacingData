namespace RacePredictor.Core;

public class RaceRunnerAttributes
{
    public RaceRunnerAttributes(int raceCardNumber, int? stallNumber, int age, RaceWeight weight, string? headGear)
    {
        RaceCardNumber = raceCardNumber;
        StallNumber = stallNumber;
        Age = age;
        Weight = weight;
        HeadGear = headGear;
    }

    public int RaceCardNumber { get; }
    public int? StallNumber { get;  }
    public int Age { get; }
    public RaceWeight Weight { get; }
    public string? HeadGear { get; }

}