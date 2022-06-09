using HtmlAgilityPack;

namespace RacePredictor.Core.RacingPost;

internal abstract class RunnerParser
{
    protected RaceEntity[] AnchorNodesToEntities(IEnumerable<HtmlNode> htmlNodes) =>
        htmlNodes.Select(n =>
                new RaceEntity(
                    @"/(\d+)/".GetMatch(n.GetAttributeValue("href", string.Empty)).AsInt(),
                    n.InnerText.TrimAllWhiteSpace()))
            .ToArray();

    protected int?[] ToRatings(IEnumerable<string> texts) => texts.Select(s => s.AsOptionalInt()).ToArray();
}