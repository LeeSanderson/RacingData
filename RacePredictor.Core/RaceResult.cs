namespace RacePredictor.Core;

public class RaceResult
{
    public RaceResult(RaceEntity course, RaceEntity race, RaceAttributes attributes, RaceResultRunner[] runners)
    {
        Course = course;
        Race = race;
        Attributes = attributes;
        Runners = runners;
    }

    public RaceEntity Course { get; }
    public RaceEntity Race { get; }
    public RaceAttributes Attributes { get; }
    public RaceResultRunner[] Runners { get; }
}