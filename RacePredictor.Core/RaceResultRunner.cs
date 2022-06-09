namespace RacePredictor.Core;

public class RaceResultRunner
{
    public RaceResultRunner(
        RaceEntity horse,
        RaceEntity jockey,
        RaceEntity trainer,
        RaceRunnerAttributes attributes,
        RaceResultRunnerStats statistics,
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
    public RaceResultRunnerStats Statistics { get; }
    public RaceResultRunnerResults Results { get; }
}