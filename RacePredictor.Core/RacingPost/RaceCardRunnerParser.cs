using System.Globalization;
using System.Text.RegularExpressions;
using HtmlAgilityPack;

namespace RacePredictor.Core.RacingPost;

internal partial class RaceCardRunnerParser : RunnerParser
{
    private static readonly Regex AgeRegex = AgeRegexGenerator();
    private static readonly Regex WeightRegex = WeightRegexGenerator();
    private static readonly Regex HeadgearRegex = HeadgearRegexGenerator();

    private readonly HtmlNodeFinder _find;

    public RaceCardRunnerParser(HtmlDocument document)
    {
        _find = new HtmlNodeFinder(document.DocumentNode);
    }

    public IEnumerable<RaceRunner> Parse()
    {
        var rowNodes = _find.AnyElement().WithAttribute("data-testid", "Container__RunnerRowDesktop").GetNodes();
        var seenHorseIds = new HashSet<int>();

        foreach (var row in rowNodes)
        {
            var rowFind = new HtmlNodeFinder(row);

            var horseAnchor = rowFind.Optional().Anchor().WithAttribute("data-testid", "Link__Horse").GetNode();
            if (horseAnchor is null)
            {
                continue;
            }

            var horse = AnchorToNamedEntity(horseAnchor);
            if (!seenHorseIds.Add(horse.Id))
            {
                continue;
            }

            var (cardNumber, draw, isNonRunner) = GetCardNumberAndDraw(rowFind);
            if (isNonRunner)
            {
                continue;
            }


            var jockey = ResolveEntity(rowFind, "Link__Jockey", new RaceEntity(0, "Unknown Jockey"));
            var trainer = ResolveEntity(rowFind, "Link__Trainer", new RaceEntity(0, "Unknown Trainer"));

            var rowText = row.InnerText.TrimAllWhiteSpace();
            var age = ExtractAge(rowText);
            var weight = ExtractWeight(rowText);
            var headgear = ExtractHeadgear(row);
            var stats = ExtractStats(rowFind);

            yield return new RaceRunner(
                horse,
                jockey,
                trainer,
                new RaceRunnerAttributes(cardNumber, draw, age, weight, headgear),
                stats);
        }
    }

    private static RaceEntity ResolveEntity(HtmlNodeFinder rowFind, string testId, RaceEntity fallback)
    {
        var node = rowFind.Optional().Anchor().WithAttribute("data-testid", testId).GetNode();
        return node != null ? AnchorToNamedEntity(node) : fallback;
    }

    private static RaceEntity AnchorToNamedEntity(HtmlNode anchor)
    {
        // Race-card anchors wrap the name in <span> elements and may also contain <sup> badges
        // (jockey booking count, trainer win-rate). Take only the span content as the name.
        var id = @"/(\d+)/".GetMatch(anchor.GetAttributeValue("href", string.Empty)).AsInt();
        var spans = anchor.SelectNodes(".//span");
        var name = spans is null
            ? anchor.InnerText.TrimAllWhiteSpace()
            : string.Join(' ', spans.Select(s => s.InnerText.TrimAllWhiteSpace()).Where(t => t.Length > 0));
        return new RaceEntity(id, name);
    }

    private static (int cardNumber, int? draw, bool isNonRunner) GetCardNumberAndDraw(HtmlNodeFinder rowFind)
    {
        var runnerNumberNode = rowFind.Optional().AnyElement().WithAttribute("data-testid", "Container__RunnerNumber").GetNode();
        if (runnerNumberNode is null)
        {
            return (0, null, true);
        }

        var scoped = new HtmlNodeFinder(runnerNumberNode);
        var spans = scoped.Element("span").GetNodes();
        if (spans.Length == 0)
        {
            return (0, null, true);
        }

        var cardText = spans[0].InnerText.TrimAllWhiteSpace();
        if (string.IsNullOrEmpty(cardText) ||
            cardText.Equals("NR", StringComparison.OrdinalIgnoreCase) ||
            cardText.StartsWith("R", StringComparison.OrdinalIgnoreCase))
        {
            return (0, null, true);
        }

        if (!int.TryParse(cardText, out var cardNumber))
        {
            return (0, null, true);
        }

        int? draw = null;
        if (spans.Length > 1)
        {
            var drawText = spans[1].InnerText.TrimAllWhiteSpace().TrimParentheses();
            draw = drawText.AsOptionalInt();
        }

        return (cardNumber, draw, false);
    }

    private static int ExtractAge(string rowText)
    {
        var m = AgeRegex.Match(rowText);
        return m.Success ? int.Parse(m.Groups[1].Value, CultureInfo.InvariantCulture) : 0;
    }

    private static RaceWeight ExtractWeight(string rowText)
    {
        var m = WeightRegex.Match(rowText);
        return m.Success
            ? new RaceWeight(
                int.Parse(m.Groups[1].Value, CultureInfo.InvariantCulture),
                int.Parse(m.Groups[2].Value, CultureInfo.InvariantCulture))
            : new RaceWeight(0, 0);
    }

    private static string? ExtractHeadgear(HtmlNode rowNode)
    {
        // Headgear is a short lowercase code (e.g., "t", "b", "p", "v", "tb", "tp") in a small <span>
        // sibling near the days-since-last-run sup. There's no data-testid, so scan spans inside the
        // horse-info section for the first short-alpha-only span that isn't a known label.
        var horseInfo = rowNode.SelectSingleNode(".//*[@data-testid='Container__HorseInfo']");
        if (horseInfo == null)
        {
            return null;
        }


        foreach (var span in horseInfo.SelectNodes(".//span") ?? Enumerable.Empty<HtmlNode>())
        {
            // Skip spans with children — we only want leaf spans.
            if (span.ChildNodes.Any(c => c.NodeType == HtmlNodeType.Element))
            {
                continue;
            }


            var text = span.InnerText.TrimAllWhiteSpace();
            if (text.Length == 0)
            {
                continue;
            }


            if (HeadgearRegex.IsMatch(text) && text != "yo" && text != "st" && text != "lb")
            {
                return text;
            }
        }
        return null;
    }

    private static RaceRunnerStats ExtractStats(HtmlNodeFinder rowFind)
    {
        var statsNode = rowFind.Optional().AnyElement().WithAttribute("data-testid", "Container__RunnerStats").GetNode();
        var text = statsNode?.InnerText ?? string.Empty;
        var or = ExtractIntStat(text, "OR");
        var ts = ExtractIntStat(text, "TS");
        var rpr = ExtractIntStat(text, "RPR");
        return new RaceRunnerStats(new RaceOdds("SP"), or, rpr, ts);
    }

    private static int? ExtractIntStat(string text, string label)
    {
        var m = Regex.Match(text, $@"{label}\s*:\s*(-|\d+)");
        if (!m.Success)
        {
            return null;
        }

        var v = m.Groups[1].Value;
        return v == "-" ? null : int.Parse(v, CultureInfo.InvariantCulture);
    }

    [GeneratedRegex(@"(\d+)yo", RegexOptions.Compiled)]
    private static partial Regex AgeRegexGenerator();
    [GeneratedRegex(@"(\d+)st\s+(\d+)lb", RegexOptions.Compiled)]
    private static partial Regex WeightRegexGenerator();
    [GeneratedRegex(@"^[a-z]{1,3}$", RegexOptions.Compiled)]
    private static partial Regex HeadgearRegexGenerator();

}
