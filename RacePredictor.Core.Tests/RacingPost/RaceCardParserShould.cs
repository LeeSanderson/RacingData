using System.Text.RegularExpressions;
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
    }

    [Fact]
    public async Task ParseKemptonRaceCardAndCorrectlyExtractHeadgear()
    {
        var actualRaceParseResult = await GetRaceCard("racecard_kempton_20260520_2000_headgear.html");

        actualRaceParseResult.Runners.Length.Should().Be(11);
        var headgearCount = actualRaceParseResult.Runners.Count(r => !string.IsNullOrEmpty(r.Attributes.HeadGear));
        headgearCount.Should().Be(6);

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
    public async Task FallBackToDefaultOddsWhenRunnerHasNoForecast()
    {
        var html = ResourceLoader.ReadRacingPostExampleResource("racecard_kempton_20260520_2000_headgear.html");
        var modified = RemoveForecastForHorse(html, 7374167);

        var card = await new RaceCardParser().Parse(modified);

        var rockIguana = card.Runners.Single(r => r.Horse.Id == 7374167);
        rockIguana.Statistics.Odds.FractionalOdds.Should().Be("SP");
        rockIguana.Statistics.Odds.DecimalOdds.Should().BeNull();

        // Other runners are unaffected and still receive their forecast.
        card.Runners.Single(r => r.Horse.Id == 4518765).Statistics.Odds.FractionalOdds.Should().Be("6/1");
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
        // Equivalent to the legacy Windsor Arabian-races test: a card whose runners do not yet have
        // an official rating. Every horse in a maiden is unrated, so OR must be null for all.
        var actualRaceParseResult = await GetRaceCard("racecard_gowran_park_20260520_1820_unrated.html");

        actualRaceParseResult.Runners.Length.Should().Be(15);
        actualRaceParseResult.Runners.Should().OnlyContain(r => r.Statistics.OfficialRating == null);
    }

    [Fact]
    public async Task ExcludeReservesFromParsedRunners()
    {
        // Synthesise a reserve by retitling the first runner's card number to "R1".
        var html = ResourceLoader.ReadRacingPostExampleResource("racecard_yarmouth_20260520_1910.html");
        var modified = MarkFirstRunnerNumberAsReserve(html);

        var card = await new RaceCardParser().Parse(modified);
        card.Runners.Length.Should().Be(5);
        card.Runners.Should().NotContain(r => r.Horse.Name == "Relocal FR");
    }

    [Fact]
    public async Task FallBackToUnknownJockeyWhenJockeyLinkMissing()
    {
        // Synthesise a missing-jockey row by retagging the first runner's jockey anchor so the
        // parser cannot locate it.
        var html = ResourceLoader.ReadRacingPostExampleResource("racecard_yarmouth_20260520_1910.html");
        var modified = RemoveFirstRunnerJockey(html);

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
    public async Task FallBackToZeroWeightWhenWeightDigitsMissing()
    {
        // Synthesise a missing-weight row by emptying the digits inside the first runner's
        // "Xst Ylb" weight markup so the parser's regex cannot match.
        var html = ResourceLoader.ReadRacingPostExampleResource("racecard_yarmouth_20260520_1910.html");
        var modified = RemoveFirstRunnerWeight(html);

        var card = await new RaceCardParser().Parse(modified);
        card.Runners.Length.Should().Be(6);
        var firstByCard = card.Runners.OrderBy(r => r.Attributes.RaceCardNumber).First();
        firstByCard.Attributes.Weight.TotalPounds.Should().Be(0);
        card.Runners.Count(r => r.Attributes.Weight.TotalPounds == 0).Should().Be(1);
    }

    private static async Task<RaceCard> GetRaceCard(string resourceFileName)
    {
        var raceResultHtmlPage = ResourceLoader.ReadRacingPostExampleResource(resourceFileName);
        var parser = new RaceCardParser();
        return await parser.Parse(raceResultHtmlPage);
    }

    private static string MarkFirstRunnerNumberAsReserve(string html)
    {
        var rowIdx = html.IndexOf("Container__RunnerRowDesktop", StringComparison.Ordinal);
        var pattern = new Regex(@"(Container__RunnerNumber[^>]*>\s*<div[^>]*>\s*<span[^>]*>)(\d+)(</span>)");
        var match = pattern.Match(html, rowIdx);
        if (!match.Success)
        {
            throw new InvalidOperationException("Could not find first runner number span to mutate.");
        }
        var replacement = $"{match.Groups[1].Value}R{match.Groups[2].Value}{match.Groups[3].Value}";
        return html[..match.Index] + replacement + html[(match.Index + match.Length)..];
    }

    private static string RemoveForecastForHorse(string html, int horseId)
    {
        // Rename only the betting-forecast anchor for this horse (the runner-row Link__Horse anchor
        // for the same id is left intact) so the forecast parser no longer matches it.
        var pattern = new Regex($"Link__BettingForecastHorse(\"[^>]*?href=\"/profile/horse/{horseId}/)");
        if (!pattern.IsMatch(html))
        {
            throw new InvalidOperationException($"Could not find forecast anchor for horse {horseId} to remove.");
        }
        // The race-card page renders its content twice, so neutralise every copy of the anchor.
        return pattern.Replace(html, "Link__BettingForecastHorseRemoved$1");
    }

    private static string RemoveGoingLink(string html) =>
        html.Replace("data-testid=\"Link__Going\"", "data-testid=\"Link__GoingRemoved\"",
            StringComparison.Ordinal);

    private static string RemoveFirstRunnerJockey(string html)
    {
        var rowIdx = html.IndexOf("Container__RunnerRowDesktop", StringComparison.Ordinal);
        const string Marker = "data-testid=\"Link__Jockey\"";
        var idx = html.IndexOf(Marker, rowIdx, StringComparison.Ordinal);
        if (idx < 0)
        {
            throw new InvalidOperationException("Could not find first jockey link to remove.");
        }
        return html[..idx] + "data-testid=\"Link__JockeyRemoved\"" + html[(idx + Marker.Length)..];
    }

    private static string RemoveFirstRunnerWeight(string html)
    {
        var rowIdx = html.IndexOf("Container__RunnerRowDesktop", StringComparison.Ordinal);
        var pattern = new Regex(@"<span[^>]*>\d+</span>st\s+<span[^>]*>\d+</span>lb");
        var match = pattern.Match(html, rowIdx);
        if (!match.Success)
        {
            throw new InvalidOperationException("Could not find first runner weight markup to remove.");
        }
        return html[..match.Index] + "<span></span>st <span></span>lb" + html[(match.Index + match.Length)..];
    }
}
