using System.ComponentModel.DataAnnotations;
using RacePredictor.Core.RacingPost;

namespace RacePredictor.Core.Tests.RacingPost;

public class NextDataRaceCardReaderShould
{
    // A self-contained, schema-valid runner used as the baseline for the structural-failure tests;
    // each test mutates exactly one aspect of it.
    private const string ValidRunner =
        "{\"horseId\":555,\"horseName\":\"Synthetic\",\"countryOrigin\":\"GB\"," +
        "\"jockeyId\":11,\"jockeyName\":\"J Test\",\"trainerId\":22,\"trainerName\":\"T Test\"," +
        "\"ownerId\":777,\"ownerName\":\"O Test\"," +
        "\"sireName\":\"S Test\",\"sireCountry\":\"GB\",\"damName\":\"D Test\"," +
        "\"age\":5,\"startNumber\":1,\"draw\":3,\"formattedWeightStones\":9,\"formattedWeightPounds\":7," +
        "\"daysSinceLastRun\":\"21\",\"formFiguresData\":[{\"figure\":\"1\",\"position\":0}]," +
        "\"officialRatingToday\":70,\"rpPostmark\":80,\"rpTopspeed\":60,\"horseHeadGear\":\"t\"," +
        "\"forecastOddsValue\":4,\"nonRunner\":false,\"irishReserve\":false}";

    private static string WrapScript(string scriptContent) =>
        $"<html><head></head><body><script id=\"__NEXT_DATA__\" type=\"application/json\">{scriptContent}</script></body></html>";

    private static string WrapDocument(string runnersArrayJson, string raceJson = "{\"raceId\":1,\"courseId\":\"2\",\"countryCode\":\"GB\"}") =>
        WrapScript(
            "{\"props\":{\"pageProps\":{\"initialState\":{\"racePage\":{\"data\":{\"race\":"
            + raceJson + ",\"runners\":" + runnersArrayJson + "}}}}}}");

    [Fact]
    public void ExposeARunnerLookedUpByHorseIdWithItsOverlappingFields()
    {
        var html = ResourceLoader.ReadRacingPostExampleResource("racecard_yarmouth_20260520_1910.html");

        var view = new NextDataRaceCardReader().Read(html);

        // Relocal FR — card number 1 on the Yarmouth card (FR suffix because countryOrigin != race country GB).
        var relocal = view.RunnerByHorseId(7462327);
        relocal.Should().NotBeNull();
        relocal!.HorseName.Should().Be("Relocal FR");
        relocal.JockeyId.Should().Be(94575);
        relocal.JockeyName.Should().Be("George Wood");
        relocal.RaceCardNumber.Should().Be(1);
        relocal.Draw.Should().Be(4);
        relocal.Age.Should().Be(4);
        relocal.Weight.Stones.Should().Be(9);
        relocal.Weight.Pounds.Should().Be(9);
        relocal.DaysSinceLastRun.Should().Be(32);
        relocal.FormFigures.Should().Be("3-1958");
        relocal.OfficialRating.Should().Be(70);
        relocal.RacingPostRating.Should().Be(84);
        relocal.TopSpeedRating.Should().Be(46);
        relocal.HeadGear.Should().BeNull();             // Relocal wears no headgear
        relocal.ForecastFractionalOdds.Should().Be("7/1");
        relocal.ForecastDecimalOdds.Should().Be(8.0);   // forecast "7/1" -> decimal 8.0
        relocal.OwnerId.Should().Be(372779);
        relocal.OwnerName.Should().Be("K Shenton & D Cunha");
        relocal.SireName.Should().Be("Siyouni");
        relocal.SireCountry.Should().Be("FR");
        relocal.DamName.Should().Be("Inconceivable");
    }

    [Fact]
    public void ExposeTheStaticHeadgearCodeAndFractionalForecastPrice()
    {
        var html = ResourceLoader.ReadRacingPostExampleResource("racecard_kempton_20260520_2000_headgear.html");

        var view = new NextDataRaceCardReader().Read(html);

        var rockIguana = view.RunnerByHorseId(7374167);
        rockIguana.Should().NotBeNull();
        rockIguana!.HeadGear.Should().Be("h");
        rockIguana.ForecastFractionalOdds.Should().Be("11/2");
        rockIguana.ForecastDecimalOdds.Should().BeApproximately(6.5, 0.001);

        // A runner with no headgear is a clean null, not an empty string.
        view.Runners.Should().Contain(r => r.HeadGear == null);
    }

    [Theory]
    [InlineData("racecard_yarmouth_20260520_1910.html")]
    [InlineData("racecard_happyvalley_20260520_1140.html")]
    [InlineData("racecard_kempton_20260520_2000_headgear.html")]
    [InlineData("racecard_warwick_20260520_1700_hurdles.html")]
    [InlineData("racecard_gowran_park_20260520_1820_unrated.html")]
    public async Task ReproduceTheOverlappingFieldsTheDomParserProduces(string fixture)
    {
        var html = ResourceLoader.ReadRacingPostExampleResource(fixture);
        var domCard = await new RaceCardParser().Parse(html);

        var view = new NextDataRaceCardReader().Read(html);

        // The reader exposes every entry; the active (non-excluded) set must match the DOM parser's.
        view.Runners.Count(r => !r.IsNonRunner).Should().Be(domCard.Runners.Length);

        foreach (var dom in domCard.Runners)
        {
            var runner = view.RunnerByHorseId(dom.Horse.Id);
            runner.Should().NotBeNull($"the DOM runner {dom.Horse.Name} should be present in the view");
            runner!.IsNonRunner.Should().BeFalse();

            runner.HorseName.Should().Be(dom.Horse.Name);
            runner.JockeyId.Should().Be(dom.Jockey.Id);
            runner.JockeyName.Should().Be(dom.Jockey.Name);
            runner.TrainerId.Should().Be(dom.Trainer.Id);
            runner.RaceCardNumber.Should().Be(dom.Attributes.RaceCardNumber);
            runner.Draw.Should().Be(dom.Attributes.StallNumber);
            runner.Weight.Stones.Should().Be(dom.Attributes.Weight.Stones);
            runner.Weight.Pounds.Should().Be(dom.Attributes.Weight.Pounds);
            runner.DaysSinceLastRun.Should().Be(dom.Attributes.DaysSinceLastRun);
            runner.FormFigures.Should().Be(dom.Attributes.FormFigures);
            runner.OfficialRating.Should().Be(dom.Statistics.OfficialRating);
            runner.RacingPostRating.Should().Be(dom.Statistics.RacingPostRating);

            // Age, TopSpeedRating and TrainerName are deliberately NOT cross-checked against the DOM:
            // the DOM parser is buggy on each, and the JSON reader is authoritative. These are pinned
            // to known-good values in their own tests below.
            //  - Age: the DOM `(\d+)yo` row-text regex mis-fires (reads 13 for a 3yo at Gowran).
            //  - TopSpeedRating: the DOM `(-|\d+)` regex discards negative ratings (-5 -> null).
            //  - TrainerName: HtmlAgilityPack leaves entities undecoded ("... &amp; ..." in the name).

            if (dom.Statistics.Odds.DecimalOdds.HasValue)
            {
                runner.ForecastDecimalOdds.Should().BeApproximately(dom.Statistics.Odds.DecimalOdds.Value, 0.02);
            }
        }
    }

    [Fact]
    public void ReadAgesCorrectlyWhereTheDomRegexIsUnreliable()
    {
        var html = ResourceLoader.ReadRacingPostExampleResource("racecard_gowran_park_20260520_1820_unrated.html");

        var view = new NextDataRaceCardReader().Read(html);

        view.RunnerByHorseId(7900527)!.Age.Should().Be(3);  // Chamonix
        view.RunnerByHorseId(8179300)!.Age.Should().Be(4);  // Loughrea
        view.RunnerByHorseId(7152226)!.Age.Should().Be(6);  // Ryans Hope
    }

    [Fact]
    public void ReadNegativeTopSpeedRatingsTheDomRegexDiscards()
    {
        var html = ResourceLoader.ReadRacingPostExampleResource("racecard_gowran_park_20260520_1820_unrated.html");

        var view = new NextDataRaceCardReader().Read(html);

        view.RunnerByHorseId(7627171)!.TopSpeedRating.Should().Be(-5);   // Zammawar — genuine negative TSR
        view.RunnerByHorseId(8236301)!.TopSpeedRating.Should().Be(9);    // Hello Garda — positive
        view.RunnerByHorseId(9254433)!.TopSpeedRating.Should().BeNull(); // Little Wing — "-" (unrated)
    }

    [Fact]
    public void ExposeCleanTrainerNamesTheDomLeavesHtmlEncoded()
    {
        var html = ResourceLoader.ReadRacingPostExampleResource("racecard_warwick_20260520_1700_hurdles.html");

        var view = new NextDataRaceCardReader().Read(html);

        view.Runners.Should().Contain(r => r.TrainerName == "Kim Bailey & Mat Nicholls");
        view.Runners.Should().NotContain(r => r.TrainerName != null && r.TrainerName.Contains("&amp;"));
    }

    [Fact]
    public void ExposeRaceLevelIdentity()
    {
        var html = ResourceLoader.ReadRacingPostExampleResource("racecard_yarmouth_20260520_1910.html");

        var view = new NextDataRaceCardReader().Read(html);

        view.CourseId.Should().Be(104);
        view.RaceId.Should().Be(918820);
        view.RaceCountryCode.Should().Be("GB");
    }

    [Fact]
    public void ThrowNamingTheKeyWhenARaceLevelFieldIsMissing()
    {
        var html = WrapDocument("[" + ValidRunner + "]", raceJson: "{\"raceId\":1,\"courseId\":\"2\"}");

        var read = () => new NextDataRaceCardReader().Read(html);

        read.Should().Throw<ValidationException>().WithMessage("*countryCode*");
    }

    [Fact]
    public void ThrowNamingTheKeyWhenTheOwnerKeyIsMissing()
    {
        var runnerWithoutOwnerId = ValidRunner.Replace("\"ownerId\":777,", string.Empty);
        var html = WrapDocument("[" + runnerWithoutOwnerId + "]");

        var read = () => new NextDataRaceCardReader().Read(html);

        read.Should().Throw<ValidationException>().WithMessage("*ownerId*");
    }

    [Fact]
    public void ThrowNamingTheKeyWhenTheSireKeyIsMissing()
    {
        var runnerWithoutSireName = ValidRunner.Replace("\"sireName\":\"S Test\",", string.Empty);
        var html = WrapDocument("[" + runnerWithoutSireName + "]");

        var read = () => new NextDataRaceCardReader().Read(html);

        read.Should().Throw<ValidationException>().WithMessage("*sireName*");
    }

    [Fact]
    public void ThrowWhenTheNextDataScriptIsAbsent()
    {
        const string html = "<html><head></head><body><p>A page with no __NEXT_DATA__ island.</p></body></html>";

        var read = () => new NextDataRaceCardReader().Read(html);

        read.Should().Throw<ValidationException>().WithMessage("*__NEXT_DATA__*");
    }

    [Fact]
    public void ThrowWhenTheNextDataJsonIsUnparseable()
    {
        var html = WrapScript("{ this is not valid json");

        var read = () => new NextDataRaceCardReader().Read(html);

        read.Should().Throw<ValidationException>().WithMessage("*could not be parsed as JSON*");
    }

    [Fact]
    public void ThrowNamingThePathWhenTheRunnersArrayDoesNotResolve()
    {
        // The runners array is renamed, so the expected path does not resolve.
        var html = WrapScript(
            "{\"props\":{\"pageProps\":{\"initialState\":{\"racePage\":{\"data\":{"
            + "\"race\":{\"raceId\":1,\"courseId\":\"2\",\"countryCode\":\"GB\"},\"runnerz\":[" + ValidRunner + "]}}}}}}");

        var read = () => new NextDataRaceCardReader().Read(html);

        read.Should().Throw<ValidationException>().WithMessage("*runners*");
    }

    [Fact]
    public void ThrowWhenTheRunnersArrayIsEmpty()
    {
        var html = WrapDocument("[]");

        var read = () => new NextDataRaceCardReader().Read(html);

        read.Should().Throw<ValidationException>().WithMessage("*empty*");
    }

    [Fact]
    public void ThrowNamingTheKeyWhenASentinelKeyIsMissing()
    {
        var runnerWithoutHorseId = ValidRunner.Replace("\"horseId\":555,", string.Empty);
        var html = WrapDocument("[" + runnerWithoutHorseId + "]");

        var read = () => new NextDataRaceCardReader().Read(html);

        read.Should().Throw<ValidationException>().WithMessage("*horseId*");
    }

    [Fact]
    public void ThrowNamingTheKeyAndTypeWhenAConsumedFieldHasTheWrongType()
    {
        var runnerWithStringAge = ValidRunner.Replace("\"age\":5,", "\"age\":\"five\",");
        var html = WrapDocument("[" + runnerWithStringAge + "]");

        var read = () => new NextDataRaceCardReader().Read(html);

        read.Should().Throw<ValidationException>()
            .WithMessage("*age*").WithMessage("*number*");
    }

    [Fact]
    public void ExposePresentButNullValuesAsCleanNullsWithoutThrowing()
    {
        var nulledRunner = ValidRunner
            .Replace("\"draw\":3,", "\"draw\":null,")
            .Replace("\"daysSinceLastRun\":\"21\",", "\"daysSinceLastRun\":null,")
            .Replace("\"officialRatingToday\":70,", "\"officialRatingToday\":\"-\",")
            .Replace("\"rpTopspeed\":60,", "\"rpTopspeed\":null,")
            .Replace("\"ownerId\":777,", "\"ownerId\":null,")
            .Replace("\"ownerName\":\"O Test\",", "\"ownerName\":null,")
            .Replace("\"sireName\":\"S Test\",", "\"sireName\":null,")
            .Replace("\"sireCountry\":\"GB\",", "\"sireCountry\":null,")
            .Replace("\"damName\":\"D Test\",", "\"damName\":null,")
            .Replace("\"forecastOddsValue\":4,", "\"forecastOddsValue\":null,");

        var view = new NextDataRaceCardReader().Read(WrapDocument("[" + nulledRunner + "]"));

        var runner = view.RunnerByHorseId(555);
        runner.Should().NotBeNull();
        runner!.Draw.Should().BeNull();
        runner.DaysSinceLastRun.Should().BeNull();
        runner.OfficialRating.Should().BeNull();
        runner.TopSpeedRating.Should().BeNull();
        runner.ForecastDecimalOdds.Should().BeNull();
        runner.OwnerId.Should().BeNull();
        runner.OwnerName.Should().BeNull();
        runner.SireName.Should().BeNull();
        runner.SireCountry.Should().BeNull();
        runner.DamName.Should().BeNull();
    }
}
