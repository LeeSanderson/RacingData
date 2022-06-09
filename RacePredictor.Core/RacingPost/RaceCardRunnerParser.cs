using HtmlAgilityPack;


namespace RacePredictor.Core.RacingPost;

internal class RaceCardRunnerParser : RunnerParser
{
    private readonly HtmlDocument _document;
    private readonly HtmlNodeFinder _find;
    private bool[] _nonRunners = Array.Empty<bool>();

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
        var attributes = GetRaceResultRunnerAttributes().ToArray();

        for (var i = 0; i < horses.Length; i++)
        {
            if (!_nonRunners[i])
            {
                yield return new RaceRunner(
                    horses[i],
                    jocks[i],
                    trainers[i],
                    attributes[i]);
            }
        }
    }

    private IEnumerable<RaceRunnerAttributes> GetRaceResultRunnerAttributes()
    {
        var raceCardNumberTexts = GetRaceCardNumbers();
        var raceCardNumbers = raceCardNumberTexts.Select(s => IsNonRunner(s) ? 0 : s.AsInt()).ToArray();
        _nonRunners = raceCardNumberTexts.Select(IsNonRunner).ToArray();

        var stallNumbers = GetStallNumbers();
        var ages = GetAges();
        var weights = GetWeights();
        var headGears = GetHeadgear();

        for (var i = 0; i < raceCardNumbers.Length; i++)
        {
            yield return new RaceRunnerAttributes(raceCardNumbers[i], stallNumbers[i], ages[i], weights[i], headGears[i]);
        }
    }

    private string[] GetRaceCardNumbers() =>
        _find.Span()
            .WithSelector("RC-cardPage-runnerNumber-no")
            .GetDirectTexts()
            .ToArray();

    private bool IsNonRunner(string raceCardNumber) => string.Equals(raceCardNumber, "NR", StringComparison.OrdinalIgnoreCase);

    private int?[] GetStallNumbers() =>
        _find.Span()
            .WithSelector("RC-cardPage-runnerNumber-draw")
            .GetTexts()
            .Select(s => s.TrimParens().AsOptionalInt())
            .ToArray();
    
    private int[] GetAges() =>
        _find.Span()
            .WithSelector("RC-cardPage-runnerAge")
            .GetIntegers();

    private RaceWeight[] GetWeights()
    {
        var stones =
            _find.Span()
                .WithCssClass("RC-runnerWgt__carried_st")
                .GetIntegers();

        var pounds =
            _find.Span()
                .WithCssClass("RC-runnerWgt__carried_lb")
                .GetIntegers();

        return stones.Zip(pounds, (st, lbs) => new RaceWeight(st, lbs)).ToArray();
    }

    private string?[] GetHeadgear() =>
        _find.Span()
            .WithSelector("RC-cardPage-runnerHeadGear")
            .GetTexts()
            .Select(s => s.NullIfEmpty())
            .ToArray();
}