using System.Text.RegularExpressions;
using HtmlAgilityPack;

namespace RacePredictor.Core.RacingPost;

public partial class RaceCardParser : RaceParser
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
        var details = ExtractCourseDetailsParts();
        var (course, race) = GetCourseAndRace(details.RaceName);
        var classification = GetClassificationFor(race.Name, details.RaceClass, details.BandText);
        var raceAttributes = GetRaceAttributes(classification);
        var runners = GetRunners();

        return Task.FromResult(new RaceCard(course, race, raceAttributes, runners));
    }

    private (RaceEntity, RaceEntity) GetCourseAndRace(string raceName)
    {
        var canonicalUrl = _find.Element("link").WithAttribute("rel", "canonical").GetAttribute("href");
        var courseId = @"/racecards/(\d+)/".FindMatch(canonicalUrl).AsInt();
        var raceId = @"/(\d+)/?$".FindMatch(canonicalUrl).AsInt();

        var courseName = _find.Anchor().WithAttribute("data-testid", "Link__CourseHeaderName").GetText();

        return (new RaceEntity(courseId, courseName), new RaceEntity(raceId, raceName));
    }

    private CourseDetailsParts ExtractCourseDetailsParts()
    {
        var courseDetailsNode = _find.Element("h2").WithAttribute("data-testid", "Container__CourseDetails").GetNode();
        var scoped = new HtmlNodeFinder(courseDetailsNode);
        var spans = scoped.Element("span").GetNodes();

        var raceName = string.Empty;
        string? raceClass = null;
        string? bandText = null;

        foreach (var span in spans)
        {
            var text = span.InnerText.TrimAllWhiteSpace();
            if (string.IsNullOrEmpty(text))
            {
                continue;
            }

            // Entirely-parenthesised spans are metadata (alternative distance, course variant,
            // class, age/rating band, surface). Race-name spans always begin with a letter.
            if (text.StartsWith('(') && text.EndsWith(')'))
            {
                if (text.StartsWith("(Class ", StringComparison.OrdinalIgnoreCase))
                {
                    raceClass = text.TrimParentheses();
                }
                else if (text.Contains("yo", StringComparison.Ordinal) || HasRatingRange(text))
                {
                    bandText = text.TrimParentheses();
                }

                continue;
            }

            if (string.IsNullOrEmpty(raceName))
            {
                raceName = text;
            }
        }

        return new CourseDetailsParts(raceName, raceClass, bandText);
    }

    private static bool HasRatingRange(string text) => RatingRangeRegex().IsMatch(text);

    private RaceClassification GetClassificationFor(string raceName, string? splitRaceClass, string? splitBandText)
    {
        // Some race-card layouts embed `(Class N)` inside the race name; others put it in its own
        // span. Likewise for the age/rating band.
        var raceClass = splitRaceClass ?? @"\((Class\s+\d+)\)".FindMatch(raceName).NullIfEmpty();
        var bandText = splitBandText.NullIfEmpty();
        var stallsText = _find.Optional().AnyElement().WithAttribute("data-testid", "Wrapper__StallsWrapper").GetText().NullIfEmpty();
        var raceTypeLabel = _find.Optional().Element("p").WithAttribute("data-testid", "Text__RaceDetailsTitle").GetText().NullIfEmpty();

        var (ageBand, ratingBand) = GetAgeAndRatingBands(bandText);
        var pattern = GetRacePattern(raceName);

        return new RaceClassification(GetRaceType(raceName, raceTypeLabel ?? stallsText), raceClass, pattern, ratingBand, ageBand, GetRaceSexRestriction(raceName));
    }

    private sealed record CourseDetailsParts(string RaceName, string? RaceClass, string? BandText);

    [GeneratedRegex(@"\d+-\d+", RegexOptions.Compiled)]
    private static partial Regex RatingRangeRegex();

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
        _find.Optional().Anchor().WithAttribute("data-testid", "Link__Going").GetText() ?? string.Empty;

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
