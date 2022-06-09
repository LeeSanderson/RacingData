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
                    new RaceEntity(4257421, "Selene's Dream"),
                    new RaceEntity(100640, "Benoit De La Sayette"),
                    new RaceEntity(9036, "Ed Dunlop"),
                    new RaceRunnerAttributes(1, 3, 3, new RaceWeight(9, 9), null)),
                new RaceRunner(
                    new RaceEntity(3437623, "Nooo More"),
                    new RaceEntity(84857, "Luke Morris"),
                    new RaceEntity(6964, "Gay Kelleway"),
                    new RaceRunnerAttributes(2, 4, 3, new RaceWeight(9, 8), null)),
                new RaceRunner(
                    new RaceEntity(3880899, "Lord Cherry"),
                    new RaceEntity(95522, "Luke Catton"),
                    new RaceEntity(8543, "Stuart Williams"),
                    new RaceRunnerAttributes(3, 7, 3, new RaceWeight(9, 7), "t")),
                new RaceRunner(
                    new RaceEntity(3791406, "Tilsworth Ony Ta"),
                    new RaceEntity(80421, "Stevie Donohoe"),
                    new RaceEntity(35, "J R Jenkins"),
                    new RaceRunnerAttributes(4, 5, 3, new RaceWeight(9, 4), null)),
                new RaceRunner(
                    new RaceEntity(4233815, "Baileys Bling"),
                    new RaceEntity(101508, "Harry Davies"),
                    new RaceEntity(32325, "Amy Murphy"),
                    new RaceRunnerAttributes(5, 8, 3, new RaceWeight(9, 4), null)),
                new RaceRunner(
                    new RaceEntity(4249831, "St Asaph"),
                    new RaceEntity(94575, "George Wood"),
                    new RaceEntity(27045, "Mrs Ilka Gansera-Leveque"),
                    new RaceRunnerAttributes(6, 9, 3, new RaceWeight(9, 3), "b")),
                new RaceRunner(
                    new RaceEntity(3549482, "Beloved Of All"),
                    new RaceEntity(91088, "Eoin Walsh"),
                    new RaceEntity(14498, "Christine Dunnett"),
                    new RaceRunnerAttributes(7, 2, 3, new RaceWeight(9, 0), "b")),
                new RaceRunner(
                    new RaceEntity(3666410, "Torious"),
                    new RaceEntity(98602, "Laura Pearson"),
                    new RaceEntity(37949, "Kevin Philippart De Foy"),
                    new RaceRunnerAttributes(8, 6, 3, new RaceWeight(9, 0), null)),
               /* Don't include non-runners
                new RaceRunner(
                    new RaceEntity(3779994, "Bielsa's Bucket"),
                    new RaceEntity(99724, "Tyler Heard"),
                    new RaceEntity(17740, "Tim Vaughan"),
                    new RaceRunnerAttributes(0, 1, 3, new RaceWeight(9, 0), null))*/
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