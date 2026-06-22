using RacePredictor.Core.RacingPost;

namespace RacePredictor.Core.Tests.RacingPost;

public class RaceCardParserShould
{
    [Fact]
    public async Task ParseExampleHappyValleyRaceCardCorrectly()
    {
        var actualRaceParseResult = await GetRaceCard("racecard_happyvalley_20260520_1140.html");

        actualRaceParseResult.Course.Id.Should().Be(396);
        actualRaceParseResult.Course.Name.Should().Be("Happy Valley");

        actualRaceParseResult.Race.Id.Should().Be(920859);
        actualRaceParseResult.Race.Name.Should().Contain("Celosia Handicap");

        actualRaceParseResult.Attributes.Off.Should().Be(new DateTime(2026, 5, 20, 11, 40, 0));
        actualRaceParseResult.Attributes.Distance.Should().BeEquivalentTo(new RaceDistance("5f"));
        actualRaceParseResult.Attributes.Going.Should().Be("Good");
        actualRaceParseResult.Attributes.NumberOfRunners.Should().Be(12);
        actualRaceParseResult.Attributes.Classification.Class.Should().Be("Class 5");
        actualRaceParseResult.Attributes.Classification.AgeBand.Should().Be("3yo+");

        actualRaceParseResult.Runners.Length.Should().Be(12);
        var first = actualRaceParseResult.Runners[0];
        first.Horse.Id.Should().Be(4043909);
        first.Horse.Name.Should().Be("Heroic Master AUS");
        first.Jockey.Name.Should().Be("Alexis Badel");
        first.Trainer.Name.Should().Be("Y S Tsui");
        first.Attributes.RaceCardNumber.Should().Be(1);
        first.Attributes.StallNumber.Should().Be(3);
        first.Attributes.Age.Should().Be(7);
        first.Statistics.OfficialRating.Should().Be(40);
        first.Statistics.RacingPostRating.Should().Be(55);
        first.Statistics.TopSpeedRating.Should().BeNull();
    }

    [Fact]
    public async Task ParseExampleYarmouthRaceCardCorrectly()
    {
        var actualRaceParseResult = await GetRaceCard("racecard_yarmouth_20260520_1910.html");

        actualRaceParseResult.Course.Id.Should().Be(104);
        actualRaceParseResult.Course.Name.Should().Be("Yarmouth");

        actualRaceParseResult.Race.Id.Should().Be(918820);
        actualRaceParseResult.Race.Name.Should().Be("Get Raceday Ready Handicap");

        actualRaceParseResult.Attributes.Off.Should().Be(new DateTime(2026, 5, 20, 19, 10, 0));
        actualRaceParseResult.Attributes.Distance.Should().BeEquivalentTo(new RaceDistance("1m6f"));
        actualRaceParseResult.Attributes.Going.Should().Be("Good");
        actualRaceParseResult.Attributes.NumberOfRunners.Should().Be(6);
        actualRaceParseResult.Attributes.PrizeMoney.Should().Be("£4,397");
        actualRaceParseResult.Attributes.PrizeMoneyValue.Should().Be(4397m);
        actualRaceParseResult.Attributes.Classification.RaceType.Should().Be(RaceType.Other);
        actualRaceParseResult.Attributes.Classification.Class.Should().Be("Class 5");
        actualRaceParseResult.Attributes.Classification.AgeBand.Should().Be("4yo+");
        actualRaceParseResult.Attributes.Classification.RatingBand.Should().Be("0-70");

        actualRaceParseResult.Runners.Length.Should().Be(6);
        var first = actualRaceParseResult.Runners[0];
        first.Horse.Name.Should().Be("Relocal FR");
        first.Jockey.Name.Should().Be("George Wood");
        first.Attributes.RaceCardNumber.Should().Be(1);
        first.Attributes.StallNumber.Should().Be(4);
        first.Attributes.Weight.Should().BeEquivalentTo(new RaceWeight(9, 9));
        first.Attributes.DaysSinceLastRun.Should().Be(32);
        first.Attributes.FormFigures.Should().Be("3-1958");
    }

    [Fact]
    public async Task ParseKemptonRaceCardAndCorrectlyExtractHeadgear()
    {
        var actualRaceParseResult = await GetRaceCard("racecard_kempton_20260520_2000_headgear.html");

        actualRaceParseResult.Runners.Length.Should().Be(11);
        // Headgear is now read from the authoritative __NEXT_DATA__ JSON, which carries 7 wearers among
        // the active runners. The old DOM span-scanning heuristic under-counted at 6 (it missed one);
        // correcting that under-count is an expected outcome of the JSON migration, not a regression.
        var headgearCount = actualRaceParseResult.Runners.Count(r => !string.IsNullOrEmpty(r.Attributes.HeadGear));
        headgearCount.Should().Be(7);

        actualRaceParseResult.Runners
            .Where(r => !string.IsNullOrEmpty(r.Attributes.HeadGear))
            .Should().OnlyContain(r => r.Attributes.HeadGear!.Length <= 3 && r.Attributes.HeadGear!.All(char.IsLower));
    }

    [Fact]
    public async Task AssignBettingForecastOddsToRunners()
    {
        var actualRaceParseResult = await GetRaceCard("racecard_kempton_20260520_2000_headgear.html");

        var rockIguana = actualRaceParseResult.Runners.Single(r => r.Horse.Id == 7374167);
        rockIguana.Statistics.Odds.FractionalOdds.Should().Be("11/2");
        rockIguana.Statistics.Odds.DecimalOdds.Should().Be(6.5);
    }

    [Fact]
    public async Task ShareForecastPriceAcrossEveryRunnerListedUnderIt()
    {
        // One forecast price span can list several horses ("20/1 Bell Shot, Tiger Crusade"); each gets it.
        var actualRaceParseResult = await GetRaceCard("racecard_kempton_20260520_2000_headgear.html");

        var bellShot = actualRaceParseResult.Runners.Single(r => r.Horse.Id == 3609039);
        var tigerCrusade = actualRaceParseResult.Runners.Single(r => r.Horse.Id == 2783578);

        bellShot.Statistics.Odds.FractionalOdds.Should().Be("20/1");
        bellShot.Statistics.Odds.DecimalOdds.Should().Be(21);
        tigerCrusade.Statistics.Odds.FractionalOdds.Should().Be("20/1");
        tigerCrusade.Statistics.Odds.DecimalOdds.Should().Be(21);
    }

    [Fact]
    public async Task DefaultToSpWhenTheBettingForecastIsAbsent()
    {
        // Remove the betting forecast from the JSON island (the captured source) and the DOM oracle
        // alike: a card with no forecast leaves every runner at SP, and the two readings still agree.
        var html = ResourceLoader.ReadRacingPostExampleResource("racecard_kempton_20260520_2000_headgear.html");
        var modified = RemoveBettingForecast(html);

        var card = await new RaceCardParser().Parse(modified);

        card.Runners.Should().OnlyContain(r =>
            r.Statistics.Odds.FractionalOdds == "SP" && r.Statistics.Odds.DecimalOdds == null);
    }

    [Fact]
    public async Task ParseWarwickRaceCardWithExpectedHurdles()
    {
        var actualRaceParseResult = await GetRaceCard("racecard_warwick_20260520_1700_hurdles.html");

        actualRaceParseResult.Attributes.Classification.RaceType.Should().Be(RaceType.Hurdle);
        actualRaceParseResult.Race.Name.Should().Be("Love Warwick Handicap Hurdle");
    }

    [Fact]
    public async Task ParseGowranParkMaidenWithUnratedRunners()
    {
        // Every horse in a maiden is unrated, so OR must be null for all.
        var actualRaceParseResult = await GetRaceCard("racecard_gowran_park_20260520_1820_unrated.html");

        actualRaceParseResult.Runners.Length.Should().Be(15);
        actualRaceParseResult.Runners.Should().OnlyContain(r => r.Statistics.OfficialRating == null);
    }

    [Fact]
    public async Task ExcludeReservesFromParsedRunners()
    {
        // The Happy Valley card carries 14 entries in the JSON runners array, two of which are flagged
        // irishReserve (Sportic Warrior, Flying Amani). Reserve exclusion is now driven by the JSON
        // flags rather than the DOM card-number text.
        var card = await GetRaceCard("racecard_happyvalley_20260520_1140.html");

        card.Runners.Length.Should().Be(12);
        card.Runners.Should().NotContain(r => r.Horse.Id == 6107027); // Sportic Warrior
        card.Runners.Should().NotContain(r => r.Horse.Id == 7209394); // Flying Amani
    }

    [Fact]
    public async Task UseUnknownJockeyWhenTheJsonJockeyIsNull()
    {
        // Null Relocal's jockey in the JSON island (a present-but-null value, the legitimate-absence
        // case). A single runner diverging from the DOM oracle is within tolerance, so the run does
        // not abort, and the captured jockey falls back to the Unknown placeholder.
        var html = ResourceLoader.ReadRacingPostExampleResource("racecard_yarmouth_20260520_1910.html");
        var modified = html
            .Replace("\"jockeyId\":94575", "\"jockeyId\":null", StringComparison.Ordinal)
            .Replace("\"jockeyName\":\"George Wood\"", "\"jockeyName\":null", StringComparison.Ordinal);

        var card = await new RaceCardParser().Parse(modified);
        card.Runners.Length.Should().Be(6);
        card.Runners.Count(r => r.Jockey.Name == "Unknown Jockey").Should().Be(1);
        card.Runners.First(r => r.Horse.Name == "Relocal FR").Jockey.Name.Should().Be("Unknown Jockey");
    }

    [Fact]
    public async Task FallBackToEmptyGoingWhenGoingLinkMissing()
    {
        var html = ResourceLoader.ReadRacingPostExampleResource("racecard_yarmouth_20260520_1910.html");
        var modified = RemoveGoingLink(html);

        var card = await new RaceCardParser().Parse(modified);
        card.Attributes.Going.Should().BeEmpty();
    }

    [Fact]
    public async Task ParseARunnerWithANullDaysSinceLastRunFromJsonAsNull()
    {
        // No fixture has a genuine first-time runner, so synthesise one by nulling Relocal's
        // days-since-last-run in the JSON island. A present-but-null value is legitimate absence
        // (a debut runner) and must surface as a clean null rather than throw. The single-runner
        // divergence from the DOM oracle is within tolerance, so the run is not aborted.
        var html = ResourceLoader.ReadRacingPostExampleResource("racecard_yarmouth_20260520_1910.html");
        var modified = html.Replace("\"daysSinceLastRun\":\"32\"", "\"daysSinceLastRun\":null", StringComparison.Ordinal);

        var card = await new RaceCardParser().Parse(modified);

        card.Runners.Length.Should().Be(6);
        var firstTimer = card.Runners.Single(r => r.Horse.Name == "Relocal FR");
        firstTimer.Attributes.DaysSinceLastRun.Should().BeNull();

        // Every other runner keeps its days-since-last-run.
        card.Runners.Where(r => r.Horse.Name != "Relocal FR")
            .Should().OnlyContain(r => r.Attributes.DaysSinceLastRun != null);
    }

    private static async Task<RaceCard> GetRaceCard(string resourceFileName)
    {
        var raceResultHtmlPage = ResourceLoader.ReadRacingPostExampleResource(resourceFileName);
        var parser = new RaceCardParser();
        return await parser.Parse(raceResultHtmlPage);
    }

    // Neutralises the betting forecast in both the JSON island (the captured source) and the DOM
    // oracle so the two readings agree that the card has no forecast.
    private static string RemoveBettingForecast(string html) =>
        html
            .Replace("\"bettingForecast\":", "\"bettingForecastRemoved\":", StringComparison.Ordinal)
            .Replace("data-testid=\"Link__BettingForecastHorse\"", "data-testid=\"Link__BettingForecastHorseRemoved\"", StringComparison.Ordinal);

    private static string RemoveGoingLink(string html) =>
        html.Replace("data-testid=\"Link__Going\"", "data-testid=\"Link__GoingRemoved\"",
            StringComparison.Ordinal);
}
