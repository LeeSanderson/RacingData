namespace RacePredictor.Core;

public class RaceCard
{
    public RaceCard(RaceEntity course, RaceEntity race, RaceAttributes attributes, RaceRunner[] runners)
    {
        Course = course;
        Race = race;
        Attributes = attributes;
        Runners = runners;
    }

    public RaceEntity Course { get; }
    public RaceEntity Race { get; }
    public RaceAttributes Attributes { get; }
    public RaceRunner[] Runners { get; }
}