namespace RacePredictor.Core;

public class RaceWeight
{
    private const int NumberOfPoundsInOneStone = 16;

    public RaceWeight(int stones, int pounds)
    {
        Stones = stones;
        Pounds = pounds;
    }

    public int Stones { get; }
    public int Pounds { get; }
    public int TotalPounds => (Stones * NumberOfPoundsInOneStone) + Pounds;

    public override string ToString() => $"{Stones}-{Pounds}";
}
