using System.ComponentModel.DataAnnotations;
using RacePredictor.Core.RacingPost;

namespace RacePredictor.Core.Tests.RacingPost;

public class NextDataRaceResultReaderShould
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
                            new RaceRunnerStats(new RaceOdds("3/1"), null, 71, 56),
                            new RaceResultRunnerResults(ResultStatus.CompletedRace, 1, 0, 0, new TimeSpan(0, 0, 1, 4, 650))),
                        new RaceResultRunner(
                            new RaceEntity(4303314, "Monte Forte"),
                            new RaceEntity(91867, "Kevin Stott"),
                            new RaceEntity(22525, "Kevin Ryan"),
                            new RaceRunnerAttributes(3, 6, 2, new RaceWeight(9, 7), null),
                            new RaceRunnerStats(new RaceOdds("7/5F"), null, 66, 50),
                            new RaceResultRunnerResults(ResultStatus.CompletedRace, 2,  2.75, 2.75, new TimeSpan(0, 0, 1, 5, 200))),
                        new RaceResultRunner(
                            new RaceEntity(4270008, "Al Hitmi"),
                            new RaceEntity(90243, "Jason Hart"),
                            new RaceEntity(5019, "K R Burke"),
                            new RaceRunnerAttributes(1, 1, 2, new RaceWeight(9, 7), null),
                            new RaceRunnerStats(new RaceOdds("5/2"), null, 54, 36),
                            new RaceResultRunnerResults(ResultStatus.CompletedRace, 3, 3.5, 6.25, new TimeSpan(0, 0, 1, 5, 900))),
                        new RaceResultRunner(
                            new RaceEntity(4274167, "Carmentis"),
                            new RaceEntity(81166, "Andrew Mullen"),
                            new RaceEntity(22367, "Ben Haslam"),
                            new RaceRunnerAttributes(4, 4, 2, new RaceWeight(9, 2), null),
                            new RaceRunnerStats(new RaceOdds("10/1"), null, 33, 14),
                            new RaceResultRunnerResults(ResultStatus.CompletedRace, 4, 4.25, 10.5, new TimeSpan(0, 0, 1, 6, 750))),
                        new RaceResultRunner(
                            new RaceEntity(4315426, "Dixiedoodledragon"),
                            new RaceEntity(87290, "Sam James"),
                            new RaceEntity(24548, "Keith Dalgleish"),
                            new RaceRunnerAttributes(5, 3, 2, new RaceWeight(9, 2), null),
                            new RaceRunnerStats(new RaceOdds("16/1"), null, 29, 9),
                            new RaceResultRunnerResults(ResultStatus.CompletedRace, 5, 1.25, 11.75, new TimeSpan(0, 0, 1, 7, 0))),
            });

    [Fact]
    public void ReadExampleCarlisleRaceResultsCorrectly()
    {
        var actualRaceParseResult = GetRaceResult("results_carlisle_20220516_1320.html");

        actualRaceParseResult.Should().BeEquivalentTo(ExpectedCarlisleRaceParseResult);
        actualRaceParseResult.Attributes.Surface.Should().Be(RaceSurface.Turf);
    }

    [Fact]
    public void ReadExampleDoncasterRaceAsVoidRace()
    {
        var read = () => GetRaceResult("result_doncaster_20091212_1445_void.html");

        read.Should().Throw<VoidRaceException>();
    }

    [Fact]
    public void ReadExampleLingfieldRaceAsVoidRace()
    {
        var read = () => GetRaceResult("result_lingfield_20220304_1555_void.html");

        read.Should().Throw<VoidRaceException>();
    }

    [Fact]
    public void ReadExampleBrightonRaceWithExpectedHeadgear()
    {
        var actualHeadgear = GetRaceResult("results_brighton_20220607_1300_headgear.html")
            .Runners.Select(r => r.Attributes.HeadGear);

        actualHeadgear.Should().BeEquivalentTo(new[] { "b", "b", "etb", "p", null, null, "v1", null, "v" });
    }

    [Fact]
    public void ReadExampleSouthwellRaceWithExpectedHurdles()
    {
        var actualRaceParseResult = GetRaceResult("results_southwell_20220606_1410_hurdles.html");

        actualRaceParseResult.Attributes.Classification.RaceType.Should().Be(RaceType.Hurdle);
    }

    [Fact]
    public void ReadExampleSouthwellRaceWithExpectedFallers()
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

        var actualFallers = GetRaceResult("results_southwell_20220606_1410_hurdles.html")
            .Runners.Where(r => r.Results.ResultStatus == ResultStatus.Fell).ToArray();

        actualFallers.Should().BeEquivalentTo(expectedFallers);
    }

    [Theory]
    [InlineData("results_hanshin_20220501_1940_unseated_rider.html", 17, ResultStatus.UnseatedRider)]
    [InlineData("results_wissembourg_20220501_1430_slipped_up.html", 6, ResultStatus.SlippedUp)]
    [InlineData("results_bath_20220501_1616_refused_to_race.html", 8, ResultStatus.RefusedToRace)]
    [InlineData("results_beverley_20220502_1701_pulled_up.html", 3, ResultStatus.PulledUp)]
    [InlineData("results_down_royal_20220502_1510_brought_down.html", 7, ResultStatus.BroughtDown)]
    [InlineData("results_auteuil_20220507_1641_disqualified.html", 5, ResultStatus.Disqualified)]
    [InlineData("results_killarney_20220515_1700_ran_out.html", 11, ResultStatus.RanOut)]
    [InlineData("results_stratford_20220518_1452_refused.html", 11, ResultStatus.Refused)]
    [InlineData("results_compiegne_20220406_1150_carriedout.html", 3, ResultStatus.CarriedOut)]
    [InlineData("results_sha_tin_20220416_1045_left_at_start.html", 6, ResultStatus.LeftAtStart)]
    public void ReadTheResultStatusOfANonFinishingRunner(string resourceFileName, int raceCardNumber, ResultStatus expected)
    {
        var horse = GetRaceResult(resourceFileName)
            .Runners.First(r => r.Attributes.RaceCardNumber == raceCardNumber);

        horse.Results.ResultStatus.Should().Be(expected);
    }

    [Fact]
    public void ReadExampleLesLandesRaceWithNoRaceCardNumbersUsingOrdinalPositionsInstead()
    {
        var raceCardNumbers = GetRaceResult("results_les_landes_20220508_1430_no_racecard_numbers.html")
            .Runners.Select(r => r.Attributes.RaceCardNumber);

        raceCardNumbers.Should().BeEquivalentTo(new[] { 1, 2, 3, 4, 5, 6 });
    }

    [Fact]
    public void ReadExampleWindsorRaceWithArabianRatings()
    {
        var ratings = GetRaceResult("results_windsor_20220516_1435_with_arabian_ratings.html")
            .Runners.Select(r => r.Statistics.OfficialRating);

        ratings.Should().BeEquivalentTo(new[] { 72, 67, 49, 69, 72, 63 });
    }

    [Fact]
    public void ReadExampleYorkRaceWithExpectedNumberOfRunners()
    {
        GetRaceResult("results_york_20220611_1505.html").Runners.Length.Should().Be(6);
    }

    [Fact]
    public void ReadExampleSouthwellRaceWithExpectedRaceId()
    {
        GetRaceResult("results_southwell_20260218_1655.html").Race.Id.Should().Be(911558);
    }

    [Fact]
    public void ReadExamplePunchestownRaceWithExpectedRunnersAndJockeys()
    {
        var actualRaceParseResult = GetRaceResult("results_punchestown_20260428_919174.html");

        actualRaceParseResult.Race.Id.Should().Be(919174);
        actualRaceParseResult.Course.Id.Should().Be(195);
        actualRaceParseResult.Runners.Length.Should().Be(18);
        actualRaceParseResult.Runners[0].Jockey.Name.Should().Be("Mr P W Mullins");
    }

    [Fact]
    public void KeepARunnerWhoseJockeyHasNoProfileLink()
    {
        // Charity/amateur races run with jockeys who have no Racing Post profile, as do races the site
        // has yet to fill in. The runner must survive with its jockey name and an Id of 0.
        var html = ResourceLoader.ReadRacingPostExampleResource("results_punchestown_20260428_919174.html")
            .Replace("\"jockeyUrl\":\"/profile/jockey/105088/mr-jack-paddy-carroll/\"", "\"jockeyUrl\":null", StringComparison.Ordinal);

        var result = new NextDataRaceResultReader().Read(html);

        result.Runners.Should().ContainSingle(r => r.Jockey.Id == 0)
            .Which.Jockey.Name.Should().Be("Mr Jack Paddy Carroll");
    }

    [Fact]
    public void ThrowWhenThePageHasNoNextDataIsland()
    {
        var read = () => new NextDataRaceResultReader().Read("<html><body><p>Nothing here.</p></body></html>");

        read.Should().Throw<ValidationException>().WithMessage("*__NEXT_DATA__*");
    }

    [Fact]
    public void ThrowWhenTheRunnersArrayIsMissing()
    {
        var html = ResourceLoader.ReadRacingPostExampleResource("results_carlisle_20220516_1320.html")
            .Replace("\"runners\":[", "\"runnersRenamed\":[", StringComparison.Ordinal);

        var read = () => new NextDataRaceResultReader().Read(html);

        read.Should().Throw<ValidationException>().WithMessage("*runners*");
    }

    [Fact]
    public void ThrowWhenARunnerIsMissingAConsumedKey()
    {
        var html = ResourceLoader.ReadRacingPostExampleResource("results_carlisle_20220516_1320.html")
            .Replace("\"topspeed\":", "\"topspeedRenamed\":", StringComparison.Ordinal);

        var read = () => new NextDataRaceResultReader().Read(html);

        read.Should().Throw<ValidationException>().WithMessage("*topspeed*");
    }

    [Fact]
    public void ThrowWhenTheRaceHeaderIsMissing()
    {
        var html = ResourceLoader.ReadRacingPostExampleResource("results_carlisle_20220516_1320.html")
            .Replace("\"header\":{", "\"headerRenamed\":{", StringComparison.Ordinal);

        var read = () => new NextDataRaceResultReader().Read(html);

        read.Should().Throw<ValidationException>().WithMessage("*header*");
    }

    private static RaceResult GetRaceResult(string resourceFileName) =>
        new NextDataRaceResultReader().Read(ResourceLoader.ReadRacingPostExampleResource(resourceFileName));
}
