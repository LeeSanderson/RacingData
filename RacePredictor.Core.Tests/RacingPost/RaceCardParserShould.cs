using RacePredictor.Core.RacingPost;

namespace RacePredictor.Core.Tests.RacingPost;

public class RaceCardParserShould
{
    private static readonly RaceCard ExpectedYarmouthRaceCardParseResult = 
        new(
            new RaceEntity(104, "Yarmouth"),
            new RaceEntity(812494, "Sky Sports Racing Sky 415 Handicap"),
            new RaceAttributes(
                new DateTime(2022, 6, 9, 13, 50, 0), 
                new RaceDistance("6f3y"), 
                new RaceClassification(RaceType.Other, "Class 6", null, "0-55", "3yo", RaceSexRestriction.None),
                "Good To Soft",
                8));

    [Fact]
    public async Task ParseExampleYarmouthRaceResultsCorrectly()
    {
        var raceCardHtmlPage = ResourceLoader.ReadResource("racecard_yarmourth_20220609_1350.html");
        var parser = new RaceCardParser();

        var actualRaceParseResult = await parser.Parse(raceCardHtmlPage);

        actualRaceParseResult.Should().BeEquivalentTo(ExpectedYarmouthRaceCardParseResult);
    }
}