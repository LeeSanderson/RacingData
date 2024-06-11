namespace RacePredictor.Core.Tests;

public class RaceOddsShould
{
    [Theory]
    [InlineData("", null)]
    [InlineData("No Odds", null)]
    [InlineData("&", null)]
    [InlineData("sp", null)]
    [InlineData("evens", 2.0)]
    [InlineData("evs", 2.0)]
    [InlineData("7/2", 4.5)]
    public void ConvertOddsToExpectedDecimalOdds(string factionalOdds, double? expectedDecimalOdds)
    {
        var raceOdds = new RaceOdds(factionalOdds);
        raceOdds.DecimalOdds.Should().Be(expectedDecimalOdds);
    }
}