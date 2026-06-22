namespace RacePredictor.Core;

public class RaceRunner
{
    public RaceRunner(
        RaceEntity horse,
        RaceEntity jockey,
        RaceEntity trainer,
        RaceRunnerAttributes attributes,
        RaceRunnerStats statistics,
        RaceEntity? owner = null)
    {
        Horse = horse;
        Jockey = jockey;
        Trainer = trainer;
        Attributes = attributes;
        Statistics = statistics;
        Owner = owner;
    }

    public RaceEntity Horse { get; }
    public RaceEntity Jockey { get; }
    public RaceEntity Trainer { get; }

    // Owner is a forward-only racecard fact (the JSON island is the sole capture source); it is null
    // on the DOM-oracle reading and excluded from cross-validation. Optional so the DOM parser and the
    // results layout are unaffected.
    public RaceEntity? Owner { get; }

    public RaceRunnerAttributes Attributes { get; }
    public RaceRunnerStats Statistics { get; }
}