using HtmlAgilityPack;

namespace RacePredictor.Core.RacingPost;

internal abstract class RunnerParser
{
    protected RaceEntity[] AnchorNodesToEntities(IEnumerable<HtmlNode> htmlNodes) =>
        htmlNodes.Select(AnchorNodeToEntity).ToArray();

    protected RaceEntity AnchorNodeToEntity(HtmlNode htmlNode) =>
        new(@"/(\d+)/".GetMatch(htmlNode.GetAttributeValue("href", string.Empty)).AsInt(),
            htmlNode.InnerText.TrimAllWhiteSpace());

    protected int?[] ToRatings(IEnumerable<string> texts) => texts.Select(s => s.AsOptionalInt()).ToArray();
}