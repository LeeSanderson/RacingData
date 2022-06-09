namespace RacePredictor.Core;

public class RaceResult
{
    public RaceResult(RaceEntity course, RaceEntity race, RaceAttributes raceAttributes, RaceResultRunner[] runners)
    {
        Course = course;
        Race = race;
        RaceAttributes = raceAttributes;
        Runners = runners;
    }

    public RaceEntity Course { get; }
    public RaceEntity Race { get; }
    public RaceAttributes RaceAttributes { get; }
    public RaceResultRunner[] Runners { get; }
}