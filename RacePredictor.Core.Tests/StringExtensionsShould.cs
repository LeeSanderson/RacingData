namespace RacePredictor.Core.Tests;

public class StringExtensionsShould
{
    [Theory]
    [InlineData("1m 45.5s", 1, 45, 500)]
    [InlineData("2m 53.50s", 2, 53, 500)]
    [InlineData("48.32s", 0, 48, 320)]
    public void ConvertStingValueToExpectedTimeSpan(string value, int expectedMinutes, int expectedSeconds, int expectedMilliseconds) =>
        value.AsTimeSpan().Should().Be(new TimeSpan(0, 0, expectedMinutes, expectedSeconds, expectedMilliseconds));

    [Theory]
    [InlineData("2022-02-07", 2022, 02, 07, 2022, 02, 07)]
    [InlineData("2022-02-07-2022-04-29", 2022, 02, 07, 2022, 04, 29)]
    public void ParseValidDateRange(string value, int startYear, int startMonth, int startDay, int endYear, int endMonth, int endDay)
    {
        var expectedStartDate = new DateOnly(startYear, startMonth, startDay);
        var expectedEndDate = new DateOnly(endYear, endMonth, endDay);

        var (start, end) = value.ToRange();

        start.Should().Be(expectedStartDate);
        end.Should().Be(expectedEndDate);
    }

    [Fact]
    public void ThrowErrorForInvalidDateRange() =>
        Assert.Throws<Exception>(() => "not-a-range".ToRange());
}
