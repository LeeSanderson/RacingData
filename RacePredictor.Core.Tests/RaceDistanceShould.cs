namespace RacePredictor.Core.Tests;

public class RaceDistanceShould
{
    [Fact]
    public void CorrectlyParseADistanceContainingMiles()
    {
        var raceDistance = new RaceDistance("2m");

        raceDistance.Distance.Should().Be("2m");
        raceDistance.DistanceInFurlongs.Should().Be(16);
        raceDistance.DistanceInMeters.Should().Be(3217);
        raceDistance.DistanceInYards.Should().Be(3520);
    }

    [Fact]
    public void CorrectlyParseADistanceContainingFurlongs()
    {
        var raceDistance = new RaceDistance("16f");

        raceDistance.Distance.Should().Be("16f");
        raceDistance.DistanceInFurlongs.Should().Be(16);
        raceDistance.DistanceInMeters.Should().Be(3217);
        raceDistance.DistanceInYards.Should().Be(3520);
    }

    [Fact]
    public void CorrectlyParseADistanceContainingFractionalFurlongs()
    {
        var raceDistance = new RaceDistance("5½f");

        raceDistance.Distance.Should().Be("5½f");
        raceDistance.DistanceInFurlongs.Should().Be(5.5);
        raceDistance.DistanceInMeters.Should().Be(1105);
        raceDistance.DistanceInYards.Should().Be(1210);
    }

    [Fact]
    public void CorrectlyParseADistanceContainingMilesAndFurlongs()
    {
        var raceDistance = new RaceDistance("1m5½f");

        raceDistance.Distance.Should().Be("1m5½f");
        raceDistance.DistanceInFurlongs.Should().Be(13.5);
        raceDistance.DistanceInMeters.Should().Be(2714);
        raceDistance.DistanceInYards.Should().Be(2970);
    }
}