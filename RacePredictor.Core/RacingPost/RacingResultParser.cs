using HtmlAgilityPack;

namespace RacePredictor.Core.RacingPost;

public class RacingResultParser : RaceParser
{
    private readonly HtmlDocument _document;
    private readonly HtmlNodeFinder _find;

    public RacingResultParser()
    {
        _document = new HtmlDocument();
        _find = new HtmlNodeFinder(_document.DocumentNode);
    }

    public Task<RaceResult> Parse(string raceResultHtmlPage)
    {
        _document.LoadHtml(raceResultHtmlPage);
        var runnerCount = GetRunnerCountAndCheckIfRaceIsVoid();
        var (course, race) = GetCourseAndRace();
        var classification = GetClassificationFor(race.Name);
        var raceAttributes = GetRaceAttributes(classification, runnerCount);
        var runners = GetRunners(course, raceAttributes);

        return Task.FromResult(new RaceResult(course, race, raceAttributes, runners));
    }

    private int GetRunnerCountAndCheckIfRaceIsVoid()
    {
        var positions = _find.Span().WithSelector("text-horsePosition").GetDirectTexts().ToArray();
        if (positions.Any(s => s == "VOI"))
        {
            throw new VoidRaceException();
        }

        return positions.Length;
    }

    private (RaceEntity, RaceEntity) GetCourseAndRace()
    {
        var canonicalUrl = _find.Element("link").WithAttribute("rel", "canonical").GetAttribute("href");
        var courseId = @"/results/(\d+)/".FindMatch(canonicalUrl).AsInt();
        var raceId = @"/.*/(\d+)/".FindMatch(canonicalUrl).AsInt();

        var courseName = _find.Element("a").WithCssClass("rp-raceTimeCourseName__name").GetText();
        var raceName = _find.Element("h2").WithCssClass("rp-raceTimeCourseName__title").GetText();

        return (new RaceEntity(courseId, courseName), new RaceEntity(raceId, raceName));
    }

    private RaceResultRunner[] GetRunners(RaceEntity course, RaceAttributes raceAttributes)
    {
        var runnerParser = new RaceResultRunnerParser(_document, course, raceAttributes);
        return runnerParser.Parse().ToArray();
    }

    private RaceAttributes GetRaceAttributes(RaceClassification classification, int defaultNumberOfRunners) =>
        new(GetOff(), GetDistance(), classification, GetGoing(), GetNumberOfRunnersWith(defaultNumberOfRunners));

    private RaceClassification GetClassificationFor(string raceName)
    {
        var raceClass = _find.Optional().Span().WithCssClass("rp-raceTimeCourseName_class").GetText().TrimParentheses().NullIfEmpty();
        var (ageBand, ratingBand) = GetAgeAndRatingBands();
        var pattern = GetRacePattern(raceName);

        return new RaceClassification(GetRaceType(raceName), raceClass, pattern, ratingBand, ageBand, GetRaceSexRestriction(raceName));
    }

    private DateTime GetOff() =>
        ParseRaceDateAndTime(
            _find.Span().WithSelector("text-raceDate").GetText(),
            _find.Span().WithSelector("text-raceTime").GetText());

    private RaceDistance GetDistance() => new(_find.Span().WithSelector("block-distanceInd").GetText());

    private string? GetGoing() => _find.Optional().Span().WithCssClass("rp-raceTimeCourseName_condition").GetText();

    private int GetNumberOfRunnersWith(int defaultValue) =>
        @"(\d+) ran"
            .FindMatch(_find.Optional().Span().WithCssClass("rp-raceInfo__value rp-raceInfo__value_black").GetText())
            .AsOptionalInt() ?? defaultValue;


    private (string, string) GetAgeAndRatingBands()
    {
        var bandText = _find.Optional().Span().WithCssClass("rp-raceTimeCourseName_ratingBandAndAgesAllowed").GetText();
        return GetAgeAndRatingBands(bandText);
    }

    private RaceType GetRaceType(string raceName)
    {
        var fences = _find.Optional().Span().WithCssClass("rp-raceTimeCourseName_hurdles").GetText();
        return GetRaceType(raceName, fences);
    }
}
