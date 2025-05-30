using HtmlAgilityPack;

namespace RacePredictor.Core.RacingPost;

internal class RaceResultRunnerParser : RunnerParser
{
    private readonly HtmlDocument _document;
    private readonly RaceEntity _course;
    private readonly RaceAttributes _raceAttributes;
    private readonly HtmlNodeFinder _find;

    internal RaceResultRunnerParser(HtmlDocument document, RaceEntity course, RaceAttributes raceAttributes)
    {
        _document = document;
        _course = course;
        _raceAttributes = raceAttributes;
        _find = new HtmlNodeFinder(document.DocumentNode);
    }

    public IEnumerable<RaceResultRunner> Parse()
    {
        var horses = AnchorNodesToEntities(_find.Anchor().WithSelector("link-horseName").GetNodes());
        var jockeyNodes = _document.DocumentNode.SelectNodes(
            "//div[contains(@class, 'rp-horseTable__human_medium')]/*/a[@data-test-selector='link-jockeyName']");
        var jocks = AnchorNodesToEntities(jockeyNodes);
        var trainerNodes = _document.DocumentNode.SelectNodes(
            "//div[contains(@class, 'rp-horseTable__human_medium')]/*/a[@data-test-selector='link-trainerName']");
        var trainers = AnchorNodesToEntities(trainerNodes);
        var attributes = GetRaceResultRunnerAttributes().ToArray();
        var statistics = GetRaceResultRunnerStats().ToArray();
        var results = GetRaceResultRunnerResults().ToArray();


        for (var i = 0; i < horses.Length; i++)
        {
            yield return new RaceResultRunner(
                horses[i],
                jocks[i],
                trainers[i],
                attributes[i],
                statistics[i],
                results[i]);
        }
    }

    private IEnumerable<RaceRunnerAttributes> GetRaceResultRunnerAttributes()
    {
        var raceCardNumbers = GetRaceCardNumbers();
        var stallNumbers = GetStallNumbers();
        var ages = GetAges();
        var weights = GetWeights();
        var headGears = GetHeadgear();

        for (var i = 0; i < raceCardNumbers.Length; i++)
        {
            yield return new RaceRunnerAttributes(
                RaceCardNumberOrIndexIfNoRaceCards(raceCardNumbers, i),
                stallNumbers[i],
                ages[i],
                weights[i],
                headGears[i]);
        }
    }

    private static int RaceCardNumberOrIndexIfNoRaceCards(IReadOnlyList<int?> raceCardNumbers, int index) => raceCardNumbers[index] ?? index + 1;

    private string?[] GetHeadgear()
    {
        var weightNodes = _find.TableCell().WithCssClass("rp-horseTable__wgt").GetNodes();
        return weightNodes
            .Select(n =>
                new HtmlNodeFinder(n).Optional().Span().WithCssClass("rp-horseTable__headGear").GetText())
            .ToArray();
    }

    private RaceWeight[] GetWeights()
    {
        var stones =
            _find.Span()
                .WithSelector("horse-weight-st")
                .GetIntegers();

        var pounds =
            _find.Span()
                .WithSelector("horse-weight-lb")
                .GetIntegers();

        return stones.Zip(pounds, (st, lbs) => new RaceWeight(st, lbs)).ToArray();
    }

    private int[] GetAges() =>
        _find.TableCell()
            .WithSelector("horse-age")
            .GetIntegers();

    private int?[] GetRaceCardNumbers() =>
        _find.Span()
            .WithCssClass("rp-horseTable__saddleClothNo")
            .GetTexts()
            .Select(s => s == "." || string.IsNullOrEmpty(s) ? (int?)null : s.TrimEnd('.').AsInt())
            .ToArray();

    private int?[] GetStallNumbers() =>
        _find.Element("sup")
            .WithCssClass("rp-horseTable__pos__draw")
            .GetTexts()
            .Select(s => s.TrimParentheses().AsOptionalInt())
            .ToArray();

    private IEnumerable<RaceRunnerStats> GetRaceResultRunnerStats()
    {
        var odds = GetRaceOdds();
        var officialRatings = ToRatings(_find.Optional().TableCell().WithDataEnding("OR").GetTexts());
        if (officialRatings.Length == 0)
        {
            // Check for Arabian "ARO" rating if no official rating
            officialRatings = ToRatings(_find.Optional().TableCell().WithDataEnding("ARO").GetTexts());
            if (officialRatings.Length == 0)
            {
                throw new Exception("Unable to find official rating for race");
            }
        }

        var topSpeedRatings = ToRatings(_find.Optional().TableCell().WithDataEnding("TS").GetTexts());
        if (topSpeedRatings.Length == 0)
        {
            topSpeedRatings = Enumerable.Repeat((int?)null, officialRatings.Length).ToArray();
        }

        var racingPostRatings = ToRatings(_find.Optional().TableCell().WithDataEnding("RPR").GetTexts());
        if (racingPostRatings.Length == 0)
        {
            racingPostRatings = Enumerable.Repeat((int?)null, officialRatings.Length).ToArray();
        }

        for (var i = 0; i < odds.Length; i++)
        {
            yield return new RaceRunnerStats(odds[i], officialRatings[i], racingPostRatings[i], topSpeedRatings[i]);
        }
    }

    private RaceOdds[] GetRaceOdds() =>
        _find.Span()
            .WithCssClass("rp-horseTable__horse__price")
            .GetTexts()
            .Select(s => new RaceOdds(s))
            .ToArray();

    private IEnumerable<RaceResultRunnerResults> GetRaceResultRunnerResults()
    {
        var positionTexts = GetPositions();
        var positions = positionTexts.Select(s => CompletedRace(s) ? s.AsInt() : 0).ToArray();
        var resultStatus = positionTexts.Select(s => s.ToResultStatus()).ToArray();
        var (beatenDistances, overallBeatenDistances) = GetBeatenDistances();
        var raceTimes = CalculateRaceTimes(overallBeatenDistances);

        for (var i = 0; i < positions.Length; i++)
        {
            yield return new RaceResultRunnerResults(
                resultStatus[i],
                positions[i],
                beatenDistances[i],
                overallBeatenDistances[i],
                raceTimes[i]);
        }
    }

    private static bool CompletedRace(string racePosition) => racePosition.ToResultStatus() == ResultStatus.CompletedRace;

    private string[] GetPositions() =>
        _find.Span()
            .WithSelector("text-horsePosition")
            .GetDirectTexts()
            .ToArray();

    private (double[], double[]) GetBeatenDistances()
    {
        var positionLengthNodes = _find.Span().WithCssClass("rp-horseTable__pos__length").GetNodes();
        var beatenDistances = new List<double>();
        var overallBeatenDistances = new List<double>();

        foreach (var positionLengthNode in positionLengthNodes)
        {
            var childSpans = new HtmlNodeFinder(positionLengthNode).Span().GetTexts().ToArray();
            if (childSpans.Length == 2)
            {
                beatenDistances.Add(ToDistance(childSpans[0]));
                overallBeatenDistances.Add(ToDistance(childSpans[1]));
            }
            else
            {
                var distance = ToDistance(childSpans[0]);
                beatenDistances.Add(distance);
                overallBeatenDistances.Add(distance);
            }
        }

        return (beatenDistances.ToArray(), overallBeatenDistances.ToArray());
    }

    private static double ToDistance(string dist)
    {
        if (string.IsNullOrEmpty(dist))
        {
            return 0;
        }

        return dist
            .Replace("[", "")
            .Replace("]", "")
            .Replace("¼", ".25")
            .Replace("½", ".5")
            .Replace("¾", ".75")
            .Replace("snk", "0.2") // Short neck
            .Replace("nk", "0.3") // Neck
            .Replace("sht-hd", "0.1") // Short head
            .Replace("shd", "0.1") // Short head (alt)
            .Replace("hd", "0.2") // Head
            .Replace("nse", "0.05") // Nose
            .Replace("dht", "0") // Dead heat
            .Replace("dist", "30") // Distance
            .AsDouble();
    }

    private TimeSpan[] CalculateRaceTimes(double[] overallBeatenDistances)
    {
        var winningTime = GetWinningTime();
        var lpsScale = LengthsPerSecondScaleTable.GetLengthsPerSecondScale(
            _raceAttributes.Classification.RaceType,
            _raceAttributes.Going,
            _course.Name);

        return overallBeatenDistances.Select(d => winningTime.Add(new TimeSpan((long)(TimeSpan.TicksPerSecond * (d / lpsScale))))).ToArray();
    }

    private TimeSpan GetWinningTime()
    {
        var resultInfo =
            _document.DocumentNode.SelectSingleNode("//div[@class='rp-raceInfo']/ul/li") ??
            throw new Exception("Unable to find winning time");
        var raceInfoNodes =
            resultInfo.SelectNodes(".//span[@class='rp-raceInfo__value']") ??
            throw new Exception("Unable to find winning time child nodes");
        if (raceInfoNodes.Count is < 2 or > 3)
        {
            throw new Exception($"Unable to find winning time - unexpected number of child nodes ({raceInfoNodes.Count})");
        }

        var winningTimeText = raceInfoNodes[^2].InnerText;
        return winningTimeText.AsTimeSpan();
    }
}
