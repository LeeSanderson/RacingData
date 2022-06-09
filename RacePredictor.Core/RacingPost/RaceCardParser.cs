using HtmlAgilityPack;

namespace RacePredictor.Core.RacingPost;

public class RaceCardParser
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

        return Task.FromResult(new RaceCard(course, race));
    }

    private (RaceEntity, RaceEntity) GetCourseAndRace()
    {
        var canonicalUrl = _find.Element("link").WithAttribute("rel", "canonical").GetAttribute("href");
        var courseId = @"/racecards/(\d+)/".FindMatch(canonicalUrl).AsInt();
        var raceId = @"/.*/(\d+)$".FindMatch(canonicalUrl).AsInt();

        var courseName = _find.Element("h1").WithSelector("RC-courseHeader__name").GetText();
        var raceName = _find.Span().WithSelector("RC-header__raceInstanceTitle").GetText();

        return (new RaceEntity(courseId, courseName), new RaceEntity(raceId, raceName));
    }

}