namespace RacePredictor.Core;

public class RaceRunner
{
    public RaceRunner(RaceEntity horse)
    {
        Horse = horse;
    }

    public RaceEntity Horse { get; }
}