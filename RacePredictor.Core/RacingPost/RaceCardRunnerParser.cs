using HtmlAgilityPack;


namespace RacePredictor.Core.RacingPost;

internal class RaceCardRunnerParser : RunnerParser
{
    private readonly HtmlNodeFinder _find;
    private bool[] _nonRunners = Array.Empty<bool>();

    public RaceCardRunnerParser(HtmlDocument document)
    {
        _find = new HtmlNodeFinder(document.DocumentNode);
    }

    public IEnumerable<RaceRunner> Parse()
    {
        var horses = AnchorNodesToEntities(_find.Anchor().WithSelector("RC-cardPage-runnerName").GetNodes());
        var jocks = GetJockies(horses.Length).ToArray();
        var trainers = AnchorNodesToEntities(_find.Anchor().WithSelector("RC-cardPage-runnerTrainer-name").GetNodes());
        var attributes = GetRaceResultRunnerAttributes(horses.Length).ToArray();
        var statistics = GetRaceResultRunnerStats().ToArray();

        for (var i = 0; i < horses.Length; i++)
        {
            if (!_nonRunners[i])
            {
                yield return new RaceRunner(
                    horses[i],
                    jocks[i],
                    trainers[i],
                    attributes[i], 
                    statistics[i]);
            }
        }
    }

    private IEnumerable<RaceEntity> GetJockies(int expectedNumberOfJockies)
    {
        var infoNodes = _find.Div().WithCssClass("RC-runnerInfo_jockey").GetNodes();
        if (infoNodes.Length != expectedNumberOfJockies)
        {
            throw new Exception($"Failed to extract jockies. Expected {expectedNumberOfJockies}, but only found {infoNodes.Length}");
        }

        foreach (var infoNode in infoNodes)
        {
            var infoFinder = new HtmlNodeFinder(infoNode);
            var jockeyNode = infoFinder.Optional().Anchor().WithSelector("RC-cardPage-runnerJockey-name").GetNode();
            yield return jockeyNode != null ? AnchorNodeToEntity(jockeyNode) : new RaceEntity(0, "Unknown Jockey");
        }
    }

    private IEnumerable<RaceRunnerAttributes> GetRaceResultRunnerAttributes(int expectedNumberOfRaces)
    {
        var raceCardNumberTexts = GetRaceCardNumbers();
        var raceCardNumbers = raceCardNumberTexts.Select(s => IsNonRunnerOrReserve(s) ? 0 : s.AsInt()).ToArray();
        _nonRunners = raceCardNumberTexts.Select(IsNonRunnerOrReserve).ToArray();

        var stallNumbers = GetStallNumbers();
        var ages = GetAges();
        var weights = GetWeights(expectedNumberOfRaces).ToArray();
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

    private bool IsNonRunnerOrReserve(string raceCardNumber) => 
        string.Equals(raceCardNumber, "NR", StringComparison.OrdinalIgnoreCase) ||
        raceCardNumber.StartsWith("R", StringComparison.OrdinalIgnoreCase);

    private int?[] GetStallNumbers() =>
        _find.Span()
            .WithSelector("RC-cardPage-runnerNumber-draw")
            .GetTexts()
            .Select(s => s.TrimParentheses().AsOptionalInt())
            .ToArray();
    
    private int[] GetAges() =>
        _find.Span()
            .WithSelector("RC-cardPage-runnerAge")
            .GetIntegers();

    private IEnumerable<RaceWeight> GetWeights(int expectedNumberOfRaces)
    {
        var weightNodes = _find.Span().WithSelector("RC-cardPage-runnerWgt-carried").GetNodes();
        if (weightNodes.Length != expectedNumberOfRaces)
        {
            throw new Exception($"Failed to extract weights. Expected {expectedNumberOfRaces}, but only found {weightNodes.Length}");
        }

        foreach (var weightNode in weightNodes)
        {
            var infoFinder = new HtmlNodeFinder(weightNode);
            var stones = infoFinder.Optional().Span().WithCssClass("RC-runnerWgt__carried_st").GetText().AsOptionalInt();
            var lbs = infoFinder.Optional().Span().WithCssClass("RC-runnerWgt__carried_lb").GetText().AsOptionalInt();
            yield return stones != null ? new RaceWeight(stones.Value, lbs ?? 0) : new RaceWeight(0, 0);
        }
    }

    private string?[] GetHeadgear() =>
        _find.Span()
            .WithSelector("RC-cardPage-runnerHeadGear")
            .GetTexts()
            .Select(s => s.NullIfEmpty())
            .ToArray();

    private IEnumerable<RaceRunnerStats> GetRaceResultRunnerStats()
    {
        var officialRatings = ToRatings(_find.Span().WithSelector("RC-cardPage-runnerOr").GetTexts());
        var topSpeedRatings = ToRatings(_find.Span().WithSelector("RC-cardPage-runnerTs").GetTexts());
        var racingPostRatings = ToRatings(_find.Span().WithSelector("RC-cardPage-runnerRpr").GetTexts());

        // Odds are set by JavaScript depending on the selected betting provider
        // (hence they can't be read by the HTML agility pack)
        // Set all odds to "SP" (starting price).
        var odds = officialRatings.Select(_ => new RaceOdds("SP")).ToArray();


        for (var i = 0; i < odds.Length; i++)
        {
            yield return new RaceRunnerStats(odds[i], officialRatings[i], racingPostRatings[i], topSpeedRatings[i]);
        }
    }
}