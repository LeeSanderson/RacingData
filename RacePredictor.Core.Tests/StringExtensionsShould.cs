namespace RacePredictor.Core.Tests;

public class StringExtensionsShould
{
    [Theory]
    [InlineData("1m 45.5s", 1, 45, 500)]
    [InlineData("2m 53.50s", 2, 53, 500)]
    [InlineData("48.32s", 0, 48, 320)]
    public void ConvertStingValueToExpectedTimeSpan(string value, int expectedMinutes, int expectedSeconds, int expectedMilliseconds)
    {
        value.AsTimeSpan().Should().Be(new TimeSpan(0, 0, expectedMinutes, expectedSeconds, expectedMilliseconds));
    }
}