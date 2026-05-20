using HtmlAgilityPack;

namespace RacePredictor.Core.RacingPost;

public class RaceCardParser : RaceParser
{
    private readonly HtmlDocument _document;
    private readonly HtmlNodeFinder _find;

    public RaceCardParser()
    {
        _document = new HtmlDocument();
        _find = new HtmlNodeFinder(_document.DocumentNode);
    }

    public Task<RaceCard> Parse(string raceResultHtmlPage)
    {
        _document.LoadHtml(raceResultHtmlPage);
        var (course, race) = GetCourseAndRace();
        var classification = GetClassificationFor(race.Name);
        var raceAttributes = GetRaceAttributes(classification);
        var runners = GetRunners();

        return Task.FromResult(new RaceCard(course, race, raceAttributes, runners));
    }

    private (RaceEntity, RaceEntity) GetCourseAndRace()
    {
        var canonicalUrl = _find.Element("link").WithAttribute("rel", "canonical").GetAttribute("href");
        var courseId = @"/racecards/(\d+)/".FindMatch(canonicalUrl).AsInt();
        var raceId = @"/(\d+)/?$".FindMatch(canonicalUrl).AsInt();

        var courseName = _find.Anchor().WithAttribute("data-testid", "Link__CourseHeaderName").GetText();
        var raceName = GetCourseDetailsSpanText(0);

        return (new RaceEntity(courseId, courseName), new RaceEntity(raceId, raceName));
    }

    private string GetCourseDetailsSpanText(int index)
    {
        var courseDetailsNode = _find.Element("h2").WithAttribute("data-testid", "Container__CourseDetails").GetNode();
        var scoped = new HtmlNodeFinder(courseDetailsNode);
        var spans = scoped.Element("span").GetNodes();
        return index < spans.Length ? spans[index].InnerText.TrimAllWhiteSpace() : string.Empty;
    }

    private RaceClassification GetClassificationFor(string raceName)
    {
        var raceClass = @"\((Class\s+\d+)\)".FindMatch(raceName).NullIfEmpty();
        var bandText = GetCourseDetailsSpanText(1).TrimParentheses().NullIfEmpty();
        var stallsText = _find.Optional().AnyElement().WithAttribute("data-testid", "Wrapper__StallsWrapper").GetText().NullIfEmpty();
        var raceTypeLabel = _find.Optional().Element("p").WithAttribute("data-testid", "Text__RaceDetailsTitle").GetText().NullIfEmpty();

        var (ageBand, ratingBand) = GetAgeAndRatingBands(bandText);
        var pattern = GetRacePattern(raceName);

        return new RaceClassification(GetRaceType(raceName, raceTypeLabel ?? stallsText), raceClass, pattern, ratingBand, ageBand, GetRaceSexRestriction(raceName));
    }

    private RaceAttributes GetRaceAttributes(RaceClassification classification) =>
        new(GetOff(), GetDistance(), classification, GetGoing(), GetNumberOfRunners());

    private DateTime GetOff()
    {
        var courseHeaderInfo = _find.AnyElement().WithAttribute("data-testid", "Container__CourseHeaderInfo").GetNode();
        var scoped = new HtmlNodeFinder(courseHeaderInfo);
        var spans = scoped.Element("span").GetNodes();
        var date = spans.Length > 0 ? spans[0].InnerText.TrimAllWhiteSpace() : string.Empty;
        var time = _find.Span().WithAttribute("data-testid", "Text__CourseHeaderTime").GetText();
        return ParseRaceDateAndTime(date, time);
    }

    private RaceDistance GetDistance()
    {
        var courseDetailsNode = _find.Element("h2").WithAttribute("data-testid", "Container__CourseDetails").GetNode();
        var scoped = new HtmlNodeFinder(courseDetailsNode);
        var distance = scoped.Element("strong").GetText();
        return new RaceDistance(distance);
    }

    private string GetGoing() =>
        _find.Anchor().WithAttribute("data-testid", "Link__Going").GetText();

    private int GetNumberOfRunners() =>
        @"Runners:\s*(\d+)"
            .GetMatch(_find.AnyElement().WithAttribute("data-testid", "Container__RaceDetailsInfo").GetText())
            .AsInt();

    private RaceRunner[] GetRunners()
    {
        var runnerParser = new RaceCardRunnerParser(_document);
        return runnerParser.Parse().ToArray();
    }
}
