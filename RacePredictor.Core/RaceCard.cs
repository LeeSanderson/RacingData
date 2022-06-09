namespace RacePredictor.Core;

public class RaceCard
{
    public RaceCard(RaceEntity course, RaceEntity race, RaceAttributes attributes)
    {
        Course = course;
        Race = race;
        Attributes = attributes;
    }

    public RaceEntity Course { get; }
    public RaceEntity Race { get; }
    public RaceAttributes Attributes { get; }
}