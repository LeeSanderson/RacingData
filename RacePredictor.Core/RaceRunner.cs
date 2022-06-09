namespace RacePredictor.Core;

public class RaceRunner
{
    public RaceRunner(RaceEntity horse, RaceEntity jockey, RaceEntity trainer)
    {
        Horse = horse;
        Jockey = jockey;
        Trainer = trainer;
    }

    public RaceEntity Horse { get; }
    public RaceEntity Jockey { get; }
    public RaceEntity Trainer { get; }
}