namespace RacePredictor.Core;

public class RaceCard
{
    public RaceCard(RaceEntity course, RaceEntity race)
    {
        Course = course;
        Race = race;
    }

    public RaceEntity Course { get; }
    public RaceEntity Race { get; }
}