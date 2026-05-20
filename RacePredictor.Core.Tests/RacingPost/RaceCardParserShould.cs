using RacePredictor.Core.RacingPost;

namespace RacePredictor.Core.Tests.RacingPost;

public class RaceCardParserShould
{
    private const string LegacySkip =
        "Racing Post racecards were rebuilt as a Next.js SPA in 2025; 2022 RC-* fixtures no longer reflect production markup. " +
        "Re-instate after generating equivalent current-format fixtures.";

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

    [Fact(Skip = LegacySkip)]
    public Task ParseExampleYarmouthRaceCardCorrectly() => Task.CompletedTask;

    [Fact(Skip = LegacySkip)]
    public Task ParseExampleNottinghamRaceCardAndCorrectlyExtractHeadgear() => Task.CompletedTask;

    [Fact(Skip = LegacySkip)]
    public Task ParseExampleUttoxeterRaceCardWithExpectedHurdles() => Task.CompletedTask;

    [Fact(Skip = LegacySkip)]
    public Task ParseExampleWindsorRaceCardWithArabRatings() => Task.CompletedTask;

    [Fact(Skip = LegacySkip)]
    public Task ParseExampleRoscommonRaceCardWithReserves() => Task.CompletedTask;

    [Fact(Skip = LegacySkip)]
    public Task ParseExampleThirskRaceCardWithMissingJockies() => Task.CompletedTask;

    [Fact(Skip = LegacySkip)]
    public Task ParseExamplePerthRaceCardMissingWeights() => Task.CompletedTask;

    private static async Task<RaceCard> GetRaceCard(string resourceFileName)
    {
        var raceResultHtmlPage = ResourceLoader.ReadRacingPostExampleResource(resourceFileName);
        var parser = new RaceCardParser();
        return await parser.Parse(raceResultHtmlPage);
    }
}
