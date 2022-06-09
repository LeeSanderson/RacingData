using RacePredictor.Core.RacingPost;

namespace RacePredictor.Core.Tests.RacingPost;

public class RaceCardParserShould
{
    private static readonly RaceCard ExpectedYarmouthRaceCardParseResult = 
        new(
            new RaceEntity(104, "Yarmouth"),
            new RaceEntity(812494, "Sky Sports Racing Sky 415 Handicap"));

    [Fact]
    public async Task ParseExampleYarmouthRaceResultsCorrectly()
    {
        var raceCardHtmlPage = ResourceLoader.ReadResource("racecard_yarmourth_20220609_1350.html");
        var parser = new RaceCardParser();

        var actualRaceParseResult = await parser.Parse(raceCardHtmlPage);

        actualRaceParseResult.Should().BeEquivalentTo(ExpectedYarmouthRaceCardParseResult);
    }
}