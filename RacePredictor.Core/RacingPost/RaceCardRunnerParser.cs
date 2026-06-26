using System.Globalization;
using System.Text.RegularExpressions;
using HtmlAgilityPack;

namespace RacePredictor.Core.RacingPost;

internal partial class RaceCardRunnerParser : RunnerParser
{
    private static readonly Regex AgeRegex = AgeRegexGenerator();
    private static readonly Regex WeightRegex = WeightRegexGenerator();
    private static readonly Regex HeadgearRegex = HeadgearRegexGenerator();

    private readonly HtmlDocument _document;
    private readonly HtmlNodeFinder _find;

    public RaceCardRunnerParser(HtmlDocument document)
    {
        _document = document;
        _find = new HtmlNodeFinder(document.DocumentNode);
    }

    public IEnumerable<RaceRunner> Parse()
    {
        var forecastOdds = ParseForecastOdds(_document);
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
            var daysSinceLastRun = ExtractDaysSinceLastRun(rowFind);
            var formFigures = ExtractFormFigures(rowFind);
            var stats = ExtractStats(rowFind, forecastOdds, horse.Id);

            yield return new RaceRunner(
                horse,
                jockey,
                trainer,
                new RaceRunnerAttributes(cardNumber, draw, age, weight, headgear, daysSinceLastRun, formFigures),
                stats);
        }
    }

    private static RaceEntity ResolveEntity(HtmlNodeFinder rowFind, string testId, RaceEntity fallback)
    {
        var node = rowFind.Optional().Anchor().WithAttribute("data-testid", testId).GetNode();
        if (node is null)
        {
            return fallback;
        }

        // An undeclared jockey/trainer renders an empty anchor with a placeholder "/racecards/race/"
        // href (no id); fall back to the same "Unknown" entity the JSON capture uses so the two agree.
        var entity = AnchorToNamedEntity(node);
        return entity.Id == 0 ? fallback : entity;
    }

    private static RaceEntity AnchorToNamedEntity(HtmlNode anchor)
    {
        // Anchors may include <sup> badges (booking count, win-rate); take only <span> text as the name.
        var id = @"/(\d+)/".FindMatch(anchor.GetAttributeValue("href", string.Empty)).AsOptionalInt() ?? 0;
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
        // Headgear has no data-testid; it's a short lowercase code (e.g. "t", "tb", "p") in a leaf
        // <span>. Scan the horse-info spans for the first short-alpha-only one that isn't a known label.
        var horseInfo = rowNode.SelectSingleNode(".//*[@data-testid='Container__HorseInfo']");
        if (horseInfo == null)
        {
            return null;
        }


        foreach (var span in horseInfo.SelectNodes(".//span") ?? Enumerable.Empty<HtmlNode>())
        {
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

    private static int? ExtractDaysSinceLastRun(HtmlNodeFinder rowFind) =>
        rowFind.Optional().AnyElement().WithAttribute("data-testid", "Text__DaysSinceLastRun").GetText().AsOptionalInt();

    private static string? ExtractFormFigures(HtmlNodeFinder rowFind) =>
        rowFind.Optional().AnyElement().WithAttribute("data-testid", "Container__RunnerRowFormFigures").GetText();

    private static RaceRunnerStats ExtractStats(HtmlNodeFinder rowFind, IReadOnlyDictionary<int, RaceOdds> forecastOdds, int horseId)
    {
        var statsNode = rowFind.Optional().AnyElement().WithAttribute("data-testid", "Container__RunnerStats").GetNode();
        var text = statsNode?.InnerText ?? string.Empty;
        var or = ExtractIntStat(text, "OR");
        var ts = ExtractIntStat(text, "TS");
        var rpr = ExtractIntStat(text, "RPR");
        var odds = forecastOdds.TryGetValue(horseId, out var forecast) ? forecast : new RaceOdds("SP");
        return new RaceRunnerStats(odds, or, rpr, ts);
    }

    // In the betting forecast a single price span precedes one or more horse anchors that share it
    // (e.g. "6/1 Spicy Spangle, Taihang Scenery"). Key each anchor's horse id to the price in its
    // nearest preceding-sibling span, so a shared price fans out to every horse under it.
    private static IReadOnlyDictionary<int, RaceOdds> ParseForecastOdds(HtmlDocument document)
    {
        var map = new Dictionary<int, RaceOdds>();
        var anchors = document.DocumentNode.SelectNodes("//a[@data-testid='Link__BettingForecastHorse']");
        if (anchors is null)
        {
            return map;
        }

        foreach (var anchor in anchors)
        {
            var horseId = @"/(\d+)/".FindMatch(anchor.GetAttributeValue("href", string.Empty)).AsOptionalInt();
            if (horseId is null)
            {
                continue;
            }

            var fractional = anchor.SelectSingleNode("preceding-sibling::span[1]")?.InnerText.TrimAllWhiteSpace();
            if (string.IsNullOrEmpty(fractional))
            {
                continue;
            }

            map[horseId.Value] = new RaceOdds(fractional);
        }

        return map;
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
