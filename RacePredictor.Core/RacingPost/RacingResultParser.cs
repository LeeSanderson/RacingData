using System.Globalization;
using HtmlAgilityPack;

namespace RacePredictor.Core.RacingPost;

public class RacingResultParser
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
        CheckIfRaceIsVoid();
        var (course, race) = GetCourseAndRace();
        var runnerCount = _find.TableCell().WithSelector("horse-age").GetNodes().Length;
        var classification = GetClassificationFor(race.Name);
        var raceAttributes = GetRaceAttributes(classification, runnerCount);
        var runners = GetRunners(course, raceAttributes);

        return Task.FromResult(new RaceResult(course, race, raceAttributes, runners));
    }

    private void CheckIfRaceIsVoid()
    {
        if (_find.Span().WithSelector("text-horsePosition").GetTexts().Any(s => s == "VOI"))
            throw new VoidRaceException();
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
        var raceClass = _find.Optional().Span().WithCssClass("rp-raceTimeCourseName_class").GetText().TrimParens().NullIfEmpty();
        var (ageBand, ratingBand) = GetAgeAndRatingBands();
        var pattern = GetRacePattern(raceName);

        return new RaceClassification(GetRaceType(raceName), raceClass, pattern, ratingBand, ageBand, GetRaceSexRestriction(raceName));
    }

    private string? GetRacePattern(string raceName)
    {
        var pattern = @"((\(|\s)((G|g)rade|(G|g)roup) (\d|[A-Ca-c]|I*)(\)|\s))".FindMatch(raceName);
        if (!string.IsNullOrEmpty(pattern))
            return pattern;

        return raceName.ToLowerInvariant().ContainsAnyIgnoreCase("listed race", "(listed") ? "Listed" : null;
    }

    private DateTime GetOff()
    {
        var raceDate = _find.Span().WithSelector("text-raceDate").GetText();
        var raceTime = _find.Span().WithSelector("text-raceTime").GetText() + " PM";
        return DateTime.ParseExact(raceDate + " " + raceTime, "d MMM yyyy h:mm tt", CultureInfo.InvariantCulture);
    }

    private RaceDistance GetDistance() => new(_find.Span().WithSelector("block-distanceInd").GetText());

    private string? GetGoing() => _find.Optional().Span().WithCssClass("rp-raceTimeCourseName_condition").GetText();

    private int GetNumberOfRunnersWith(int defaultValue) =>
        @"(\d+) ran"
            .FindMatch(_find.Optional().Span().WithCssClass("rp-raceInfo__value rp-raceInfo__value_black").GetText())
            .AsOptionalInt() ?? defaultValue;


    private (string, string) GetAgeAndRatingBands()
    {
        var ageBand = string.Empty;
        var ratingBand = string.Empty;
        var bandText = _find.Optional().Span().WithCssClass("rp-raceTimeCourseName_ratingBandAndAgesAllowed").GetText();
        if (!string.IsNullOrEmpty(bandText))
        {
            var bands = bandText.TrimParens().Split(",", StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
            foreach (var band in bands)
            {
                if (band.Contains("yo"))
                    ageBand = band;
                else if (band.Contains('-'))
                    ratingBand = band;
            }
        }

        return (ageBand, ratingBand);
    }

    private RaceType GetRaceType(string raceName)
    {
        if (raceName.ContainsAnyIgnoreCase("national hunt flat"))
            return RaceType.Flat;

        var fences = _find.Optional().Span().WithCssClass("rp-raceTimeCourseName_hurdles").GetText();
        if (!string.IsNullOrEmpty(fences))
        {
            fences = fences.ToLowerInvariant();
            if (fences.Contains("hurdle"))
                return RaceType.Hurdle;

            if (fences.Contains("chase"))
                return RaceType.SteepleChase;
        }

        
        if (raceName.ContainsAnyIgnoreCase(" hurdle", "(hurdle)"))
            return RaceType.Hurdle;

        if (raceName.ContainsAnyIgnoreCase(" chase", "(chase)", "steeplechase", "steeple-chase", "steeplchase", "steepl-chase"))
            return RaceType.SteepleChase;

        return raceName.ContainsAnyIgnoreCase(" flat race", "national hunt flat") ? RaceType.Hurdle : RaceType.Other;
    }

    private RaceSexRestriction GetRaceSexRestriction(string raceName)
    {
        if (raceName.ContainsAnyIgnoreCase("entire colts & fillies", "colts & fillies"))
            return RaceSexRestriction.ColtsAndFillies;

        if (raceName.ContainsAnyIgnoreCase("fillies & mares', 'filles & mares"))
            return RaceSexRestriction.FilliesAndMares;

        if (raceName.ContainsAnyIgnoreCase("fillies"))
            return RaceSexRestriction.Fillies;

        if (raceName.ContainsAnyIgnoreCase("colts & geldings", "colts/geldings", "(c & g)"))
            return RaceSexRestriction.ColdsAndGeldings;

        if (raceName.ContainsAnyIgnoreCase("mares & geldings"))
            return RaceSexRestriction.MaresAndGeldings;

        return raceName.Contains("mares") ? RaceSexRestriction.Mares : RaceSexRestriction.None;
    }

}