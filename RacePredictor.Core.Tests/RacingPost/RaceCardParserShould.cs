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
                8),
            new []
            {
                new RaceRunner(
                    new RaceEntity(4257421, "Selene's Dream")),
                new RaceRunner(
                    new RaceEntity(3437623, "Nooo More")),
                new RaceRunner(
                    new RaceEntity(3880899, "Lord Cherry")),
                new RaceRunner(
                    new RaceEntity(3791406, "Tilsworth Ony Ta")),
                new RaceRunner(
                    new RaceEntity(4233815, "Baileys Bling")),
                new RaceRunner(
                    new RaceEntity(4249831, "St Asaph")),
                new RaceRunner(
                    new RaceEntity(3549482, "Beloved Of All")),
                new RaceRunner(
                    new RaceEntity(3666410, "Torious")),
                new RaceRunner(
                    new RaceEntity(3779994, "Bielsa's Bucket"))
            });

    [Fact]
    public async Task ParseExampleYarmouthRaceResultsCorrectly()
    {
        var raceCardHtmlPage = ResourceLoader.ReadResource("racecard_yarmourth_20220609_1350.html");
        var parser = new RaceCardParser();

        var actualRaceParseResult = await parser.Parse(raceCardHtmlPage);

        actualRaceParseResult.Should().BeEquivalentTo(ExpectedYarmouthRaceCardParseResult);
    }
}