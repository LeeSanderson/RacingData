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
                            new RaceRunnerAttributes(6, 5, 2, new RaceWeight(9, 2), null),
                            new RaceRunnerStats(new RaceOdds("3/1"), null, 79, 56),
                            new RaceResultRunnerResults(ResultStatus.CompletedRace, 1, 0, 0, new TimeSpan(0, 0, 1, 4, 650))),
                        new RaceResultRunner(
                            new RaceEntity(4303314, "Monte Forte"),
                            new RaceEntity(91867, "Kevin Stott"),
                            new RaceEntity(22525, "Kevin Ryan"),
                            new RaceRunnerAttributes(3, 6, 2, new RaceWeight(9, 7), null),
                            new RaceRunnerStats(new RaceOdds("7/5F"), null, 74, 50),
                            new RaceResultRunnerResults(ResultStatus.CompletedRace, 2,  2.75, 2.75, new TimeSpan(0, 0, 1, 5, 200))),
                        new RaceResultRunner(
                            new RaceEntity(4270008, "Al Hitmi"),
                            new RaceEntity(90243, "Jason Hart"),
                            new RaceEntity(5019, "K R Burke"),
                            new RaceRunnerAttributes(1, 1, 2, new RaceWeight(9, 7), null),
                            new RaceRunnerStats(new RaceOdds("5/2"), null, 62, 36),
                            new RaceResultRunnerResults(ResultStatus.CompletedRace, 3, 3.5, 6.25, new TimeSpan(0, 0, 1, 5, 900))),
                        new RaceResultRunner(
                            new RaceEntity(4274167, "Carmentis"),
                            new RaceEntity(81166, "Andrew Mullen"),
                            new RaceEntity(22367, "Ben Haslam"),
                            new RaceRunnerAttributes(4, 4, 2, new RaceWeight(9, 2), null),
                            new RaceRunnerStats(new RaceOdds("10/1"), null, 41, 14),
                            new RaceResultRunnerResults(ResultStatus.CompletedRace, 4, 4.25, 10.5, new TimeSpan(0, 0, 1, 6, 750))),
                        new RaceResultRunner(
                            new RaceEntity(4315426, "Dixiedoodledragon"),
                            new RaceEntity(87290, "Sam James"),
                            new RaceEntity(24548, "Keith Dalgleish"),
                            new RaceRunnerAttributes(5, 3, 2, new RaceWeight(9, 2), null),
                            new RaceRunnerStats(new RaceOdds("16/1"), null, 37, 9),
                            new RaceResultRunnerResults(ResultStatus.CompletedRace, 5, 1.25, 11.75, new TimeSpan(0, 0, 1, 7, 0))),
            });

    [Fact]
    public async Task ParseExampleCarlisleRaceResultsCorrectly()
    {
        var actualRaceParseResult = await GetRaceResult("results_carlisle_20220516_1320.html");

        actualRaceParseResult.Should().BeEquivalentTo(ExpectedCarlisleRaceParseResult);
        actualRaceParseResult.Attributes.Surface.Should().Be(RaceSurface.Turf);
    }

    [Fact]
    public async Task ParseExampleDoncasterRaceAsVoidRace()
    {
        var raceResultHtmlPage = ResourceLoader.ReadResource("result_doncaster_20091212_1445_void.html");
        var parser = new RacingResultParser();

        await Assert.ThrowsAsync<VoidRaceException>(() => parser.Parse(raceResultHtmlPage));
    }

    [Fact]
    public async Task ParseExampleBrightonRaceWithExpectedHeadgear()
    {
        var actualRaceParseResult = await GetRaceResult("results_brighton_20220607_1300_headgear.html");
        var actualHeadgear = actualRaceParseResult.Runners.Select(r => r.Attributes.HeadGear);

        actualHeadgear.Should().BeEquivalentTo(new[] { "b", "b", "etb", "p", null, null, "v1", null, "v" });
    }

    [Fact]
    public async Task ParseExampleSouthwellRaceWithExpectedHurdles()
    {
        var actualRaceParseResult = await GetRaceResult("results_southwell_20220606_1410_hurdles.html");
        actualRaceParseResult.Attributes.Classification.RaceType.Should().Be(RaceType.Hurdle);
    }

    [Fact]
    public async Task ParseExampleSouthwellRaceWithExpectedFallers()
    {
        var expectedFallers = new[]
        {
            new RaceResultRunner(
                new RaceEntity(1900082, "Phyllis"),
                new RaceEntity(88090, "Ben Poste"),
                new RaceEntity(39501, "Harriet Dickin"),
                new RaceRunnerAttributes(8, null, 6, new RaceWeight(10, 11), null),
                new RaceRunnerStats(new RaceOdds("250/1"), null, null, null),
                new RaceResultRunnerResults(ResultStatus.Fell, 0, 0, 0, new TimeSpan(0, 0, 3, 57, 800)))
        };

        var actualRaceParseResult = await GetRaceResult("results_southwell_20220606_1410_hurdles.html");
        var actualFallers = actualRaceParseResult.Runners.Where(r => r.Results.ResultStatus == ResultStatus.Fell).ToArray();

        actualFallers.Should().BeEquivalentTo(expectedFallers);
    }

    [Fact]
    public async Task ParseExampleHanshinRaceWithExpectedUnseatedRider()
    {
        var actualRaceParseResult = await GetRaceResult("results_hanshin_20220501_1940_unseated_rider.html");
        var horse = actualRaceParseResult.Runners.First(r => r.Attributes.RaceCardNumber == 17);

        horse.Results.ResultStatus.Should().Be(ResultStatus.UnseatedRider);
    }

    [Fact]
    public async Task ParseExampleWissenbourgRaceWithExpectedSlippedUpRunner()
    {
        var actualRaceParseResult = await GetRaceResult("results_wissembourg_20220501_1430_slipped_up.html");
        var horse = actualRaceParseResult.Runners.First(r => r.Attributes.RaceCardNumber == 6);

        horse.Results.ResultStatus.Should().Be(ResultStatus.SlippedUp);
    }

    [Fact]
    public async Task ParseExampleBathRaceWithExpectedRefusedToRace()
    {
        var actualRaceParseResult =  await GetRaceResult("results_bath_20220501_1616_refused_to_race.html");
        var horse = actualRaceParseResult.Runners.First(r => r.Attributes.RaceCardNumber == 8);

        horse.Results.ResultStatus.Should().Be(ResultStatus.RefusedToRace);
    }

    [Fact]
    public async Task ParseExampleBeverlyRaceWithExpectedPulledUpRunner()
    {
        var actualRaceParseResult = await GetRaceResult("results_beverley_20220502_1701_pulled_up.html");
        var horse = actualRaceParseResult.Runners.First(r => r.Attributes.RaceCardNumber == 3);

        horse.Results.ResultStatus.Should().Be(ResultStatus.PulledUp);
    }

    [Fact]
    public async Task ParseExampleDownRoyalRaceWithExpectedBroughtDownRunner()
    {
        var actualRaceParseResult = await GetRaceResult("results_down_royal_20220502_1510_brought_down.html");
        var horse = actualRaceParseResult.Runners.First(r => r.Attributes.RaceCardNumber == 7);

        horse.Results.ResultStatus.Should().Be(ResultStatus.BroughtDown);
    }

    private static async Task<RaceResult> GetRaceResult(string resourceFileName)
    {
        var raceResultHtmlPage = ResourceLoader.ReadResource(resourceFileName);
        var parser = new RacingResultParser();

        return await parser.Parse(raceResultHtmlPage);
    }
}