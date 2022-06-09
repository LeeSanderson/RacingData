using System.Globalization;
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
        var raceId = @"/.*/(\d+)$".FindMatch(canonicalUrl).AsInt();

        var courseName = _find.Element("h1").WithSelector("RC-courseHeader__name").GetText();
        var raceName = _find.Span().WithSelector("RC-header__raceInstanceTitle").GetText();

        return (new RaceEntity(courseId, courseName), new RaceEntity(raceId, raceName));
    }

    private RaceClassification GetClassificationFor(string raceName)
    {
        var raceClass = _find.Optional().Span().WithSelector("RC-header__raceClass").GetText().TrimParens().NullIfEmpty();
        var bandText = _find.Optional().Span().WithSelector("RC-header__rpAges").GetText().TrimParens().NullIfEmpty();
        var stallsText = _find.Optional().Div().WithSelector("RC-headerBox__stalls").GetText().NullIfEmpty();

        var (ageBand, ratingBand) = GetAgeAndRatingBands(bandText);
        var pattern = GetRacePattern(raceName);

        return new RaceClassification(GetRaceType(raceName, stallsText), raceClass, pattern, ratingBand, ageBand, GetRaceSexRestriction(raceName));
    }

    private RaceAttributes GetRaceAttributes(RaceClassification classification) =>
        new(GetOff(), GetDistance(), classification, GetGoing(), GetNumberOfRunners());

    private DateTime GetOff() =>
        ParseRaceDateAndTime(
            _find.Span().WithSelector("RC-courseHeader__date").GetDirectText(),
            _find.Span().WithSelector("RC-courseHeader__time").GetText());

    private RaceDistance GetDistance() => new(_find.Span().WithSelector("RC-header__raceDistance").GetText().TrimParens());

    private string GetGoing() =>
        @"Going:\s*(.+)"
            .GetMatch(_find.Div().WithSelector("RC-headerBox__going").GetText());

    private int GetNumberOfRunners() =>
        @"Runners:\s*(\d+)"
            .GetMatch(_find.Div().WithSelector("RC-headerBox__runners").GetText())
            .AsInt();

    private RaceRunner[] GetRunners()
    {
        var runnerParser = new RaceCardRunnerParser(_document);
        return runnerParser.Parse().ToArray();
    }
}