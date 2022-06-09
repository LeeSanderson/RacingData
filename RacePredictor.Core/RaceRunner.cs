namespace RacePredictor.Core;

public class RaceRunner
{
    public RaceRunner(RaceEntity horse, RaceEntity jockey, RaceEntity trainer, RaceRunnerAttributes attributes)
    {
        Horse = horse;
        Jockey = jockey;
        Trainer = trainer;
        Attributes = attributes;
    }

    public RaceEntity Horse { get; }
    public RaceEntity Jockey { get; }
    public RaceEntity Trainer { get; }
    public RaceRunnerAttributes Attributes { get; }
}