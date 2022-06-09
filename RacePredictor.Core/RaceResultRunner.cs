namespace RacePredictor.Core;

public class RaceResultRunner
{
    public RaceResultRunner(
        RaceEntity horse,
        RaceEntity jockey,
        RaceEntity trainer,
        RaceRunnerAttributes attributes,
        RaceRunnerStats statistics,
        RaceResultRunnerResults results)
    {
        Horse = horse;
        Jockey = jockey;
        Trainer = trainer;
        Attributes = attributes;
        Statistics = statistics;
        Results = results;
    }

    public RaceEntity Horse { get; }
    public RaceEntity Jockey { get; }
    public RaceEntity Trainer { get; }
    public RaceRunnerAttributes Attributes { get; }
    public RaceRunnerStats Statistics { get; }
    public RaceResultRunnerResults Results { get; }
}