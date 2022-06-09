using HtmlAgilityPack;

namespace RacePredictor.Core.RacingPost;

internal class RaceCardRunnerParser : RunnerParser
{
    private readonly HtmlDocument _document;
    private readonly HtmlNodeFinder _find;

    public RaceCardRunnerParser(HtmlDocument document)
    {
        _document = document;
        _find = new HtmlNodeFinder(document.DocumentNode);
    }

    public IEnumerable<RaceRunner> Parse()
    {
        var horses = AnchorNodesToEntities(_find.Anchor().WithSelector("RC-cardPage-runnerName").GetNodes());
        var jocks = AnchorNodesToEntities(_find.Anchor().WithSelector("RC-cardPage-runnerJockey-name").GetNodes());
        var trainers = AnchorNodesToEntities(_find.Anchor().WithSelector("RC-cardPage-runnerTrainer-name").GetNodes());

        for (var i = 0; i < horses.Length; i++)
        {
            yield return new RaceRunner(
                horses[i], 
                jocks[i],
                trainers[i]);
        }

    }
}