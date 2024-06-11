namespace RacePredictor.Core;

public class RaceRunner
{
    public RaceRunner(
        RaceEntity horse,
        RaceEntity jockey,
        RaceEntity trainer,
        RaceRunnerAttributes attributes,
        RaceRunnerStats statistics)
    {
        Horse = horse;
        Jockey = jockey;
        Trainer = trainer;
        Attributes = attributes;
        Statistics = statistics;
    }

    public RaceEntity Horse { get; }
    public RaceEntity Jockey { get; }
    public RaceEntity Trainer { get; }
    public RaceRunnerAttributes Attributes { get; }
    public RaceRunnerStats Statistics { get; }
}