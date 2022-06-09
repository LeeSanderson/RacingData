using System.Reflection;
using RacePredictor.Core.RacingPost;

namespace RacePredictor.Core.Tests.RacingPost;

public class RacingResultParserShould
{
    private static readonly RaceResult ExpectedCarlisleRaceParseResult =
        new(
            new RaceEntity(8, "Carlisle"),
            new RaceEntity(810017, "British Stallion Studs EBF Novice Stakes (GBB Race)"),
            new RaceAttributes(
                new DateTime(2022, 5, 16, 13, 20, 0),
                new RaceDistance("5f"),
                new RaceClassification(RaceType.Other, "Class 4", null, "", "2yo", RaceSexRestriction.None),
                "Good",
                5),
            new[]
            {
                        new RaceResultRunner(
                            new RaceEntity(4288203, "Queen Of Deauville"),
                            new RaceEntity(7458, "Franny Norton"),
                            new RaceEntity(39124, "Charlie & Mark Johnston"),
                            new RaceResultRunnerAttributes(6, 5, 2, new RaceWeight(9, 2), null),
                            new RaceResultRunnerStats(new RaceOdds("3/1"), null, 79, 56),
                            new RaceResultRunnerResults(1, 0, 0, new TimeSpan(0, 0, 1, 4, 650))),
                        new RaceResultRunner(
                            new RaceEntity(4303314, "Monte Forte"),
                            new RaceEntity(91867, "Kevin Stott"),
                            new RaceEntity(22525, "Kevin Ryan"),
                            new RaceResultRunnerAttributes(3, 6, 2, new RaceWeight(9, 7), null),
                            new RaceResultRunnerStats(new RaceOdds("7/5F"), null, 74, 50),
                            new RaceResultRunnerResults(2, 2.75, 2.75, new TimeSpan(0, 0, 1, 5, 200))),
                        new RaceResultRunner(
                            new RaceEntity(4270008, "Al Hitmi"),
                            new RaceEntity(90243, "Jason Hart"),
                            new RaceEntity(5019, "K R Burke"),
                            new RaceResultRunnerAttributes(1, 1, 2, new RaceWeight(9, 7), null),
                            new RaceResultRunnerStats(new RaceOdds("5/2"), null, 62, 36),
                            new RaceResultRunnerResults(3, 3.5, 6.25, new TimeSpan(0, 0, 1, 5, 900))),
                        new RaceResultRunner(
                            new RaceEntity(4274167, "Carmentis"),
                            new RaceEntity(81166, "Andrew Mullen"),
                            new RaceEntity(22367, "Ben Haslam"),
                            new RaceResultRunnerAttributes(4, 4, 2, new RaceWeight(9, 2), null),
                            new RaceResultRunnerStats(new RaceOdds("10/1"), null, 41, 14),
                            new RaceResultRunnerResults(4, 4.25, 10.5, new TimeSpan(0, 0, 1, 6, 750))),
                        new RaceResultRunner(
                            new RaceEntity(4315426, "Dixiedoodledragon"),
                            new RaceEntity(87290, "Sam James"),
                            new RaceEntity(24548, "Keith Dalgleish"),
                            new RaceResultRunnerAttributes(5, 3, 2, new RaceWeight(9, 2), null),
                            new RaceResultRunnerStats(new RaceOdds("16/1"), null, 37, 9),
                            new RaceResultRunnerResults(5, 1.25, 11.75, new TimeSpan(0, 0, 1, 7, 0))),
            });

    [Fact]
    public async Task ParseExampleCarlisleRaceResultsCorrectly()
    {
        var raceResultHtmlPage = ReadResource("results_carlisle_20220516_1320.html");
        var parser = new RacingResultParser();

        var actualRaceParseResult = await parser.Parse(raceResultHtmlPage);

        actualRaceParseResult.Should().BeEquivalentTo(ExpectedCarlisleRaceParseResult);
        actualRaceParseResult.RaceAttributes.Surface.Should().Be(RaceSurface.Turf);
    }

    [Fact]
    public async Task ParseExampleDoncasterRaceAsVoidRace()
    {
        var raceResultHtmlPage = ReadResource("result_doncaster_20091212_1445_void.html");
        var parser = new RacingResultParser();

        await Assert.ThrowsAsync<VoidRaceException>(() => parser.Parse(raceResultHtmlPage));
    }

    [Fact]
    public async Task ParseExampleBrightonRaceWithExpectedHeadgear()
    {
        var raceResultHtmlPage = ReadResource("results_brighton_20220607_1300_headgear.html");
        var parser = new RacingResultParser();

        var actualRaceParseResult = await parser.Parse(raceResultHtmlPage);
        var actualHeadgear = actualRaceParseResult.Runners.Select(r => r.Attributes.HeadGear);

        actualHeadgear.Should().BeEquivalentTo(new[] { "b", "b", "etb", "p", null, null, "v1", null, "v" });
    }

    private static string ReadResource(string fileName)
    {
        var assembly = Assembly.GetExecutingAssembly();

        var resourceName = $"{typeof(RacingResultParserShould).Namespace}.Examples.{fileName}";

        using var stream = assembly.GetManifestResourceStream(resourceName);
        if (stream == null)
            throw new Exception($"Resource {fileName} not found");

        using var reader = new StreamReader(stream);
        return reader.ReadToEnd();
    }
}