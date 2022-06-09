using HtmlAgilityPack;

namespace RacePredictor.Core.RacingPost
{
    internal class RaceResultRunnerParser
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

        private RaceEntity[] AnchorNodesToEntities(IEnumerable<HtmlNode> htmlNodes) =>
            htmlNodes.Select(n =>
                    new RaceEntity(
                        @"/(\d+)/".GetMatch(n.GetAttributeValue("href", string.Empty)).AsInt(),
                        n.InnerText.TrimAllWhiteSpace()))
                .ToArray();

        private IEnumerable<RaceResultRunnerAttributes> GetRaceResultRunnerAttributes()
        {
            var raceCardNumbers = GetRaceCardNumbers();
            var stallNumbers = GetStallNumbers();
            var ages = GetAges();
            var weights = GetWeights();
            var headGears = GetHeadgear();

            for (var i = 0; i < raceCardNumbers.Length; i++)
            {
                yield return new RaceResultRunnerAttributes(raceCardNumbers[i], stallNumbers[i], ages[i], weights[i], headGears[i]);
            }
        }

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

        private int[] GetRaceCardNumbers() => 
            _find.Span()
                .WithCssClass("rp-horseTable__saddleClothNo")
                .GetTexts()
                .Select(s => s.TrimEnd('.').AsInt())
                .ToArray();

        private int?[] GetStallNumbers() =>
            _find.Element("sup")
                .WithCssClass("rp-horseTable__pos__draw")
                .GetTexts()
                .Select(s => s.TrimParens().AsOptionalInt())
                .ToArray();

        private IEnumerable<RaceResultRunnerStats> GetRaceResultRunnerStats()
        {
            var odds = GetRaceOdds();
            var officialRatings = ToRatings(_find.TableCell().WithDataEnding("OR").GetTexts());
            var topSpeedRatings = ToRatings(_find.TableCell().WithDataEnding("TS").GetTexts());
            var racingPostRatings = ToRatings(_find.TableCell().WithDataEnding("RPR").GetTexts());

            for (var i = 0; i < odds.Length; i++)
            {
                yield return new RaceResultRunnerStats(odds[i], officialRatings[i], racingPostRatings[i], topSpeedRatings[i]);
            }
        }

        private int?[] ToRatings(IEnumerable<string> texts) => texts.Select(s => s.AsOptionalInt()).ToArray();

        private RaceOdds[] GetRaceOdds() => 
            _find.Span()
                .WithCssClass("rp-horseTable__horse__price")
                .GetTexts()
                .Select(s => new RaceOdds(s))
                .ToArray();

        private IEnumerable<RaceResultRunnerResults> GetRaceResultRunnerResults()
        {
            var positionTexts = GetPositions();
            var positions = positionTexts.Select(s => s.ContainsAnyIgnoreCase("VOI", "F") ? 0 : s.AsInt()).ToArray(); // May be "VOI" if race is void or "F" if faller. 
            var fallers = positionTexts.Select(s => string.Equals(s, "F", StringComparison.OrdinalIgnoreCase)).ToArray();
            var (beatenDistances, overallBeatenDistances) = GetBeatenDistances();
            var raceTimes = CalculateRaceTimes(overallBeatenDistances);

            for (var i = 0; i < positions.Length; i++)
            {
                yield return new RaceResultRunnerResults(
                    positions[i],
                    fallers[i],
                    beatenDistances[i], 
                    overallBeatenDistances[i], 
                    raceTimes[i]);
            }
        }

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
                return 0;

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
                throw new Exception($"Unable to find winning time - unexpected number of child nodes ({raceInfoNodes.Count})");

            var winningTimeText = raceInfoNodes[^2].InnerText;
            return winningTimeText.AsTimeSpan();
        }
    }
}
