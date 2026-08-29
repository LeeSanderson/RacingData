using System.ComponentModel.DataAnnotations;
using HtmlAgilityPack;

namespace RacePredictor.Core.RacingPost;

public class RacingDataDownloader(IHtmlLoader htmlLoader, IClock clock) : IRacingDataDownloader
{
    public async IAsyncEnumerable<string> GetResultUrls(DateOnly start, DateOnly end)
    {
        var currentDate = start;
        while (currentDate <= end)
        {
            // The course-grouped index (/results/{date}) server-renders 'results.data: null' with
            // 'error: "An error occurred"' for recent dates; the time-ordered view of the same day
            // carries the full data and yields an identical set of links on every date both render.
            var resultsUrl = $"https://www.racingpost.com/results/{currentDate:yyyy-MM-dd}/time-order";
            HtmlDocument htmlDocument;
            try
            {
                htmlDocument = await GetHtmlDocumentFrom(resultsUrl);
            }
            catch (Exception e)
            {
                throw new Exception($"Failed to load URL {resultsUrl}: {e.Message}", e);
            }

            string[] urls;
            try
            {
                urls = new NextDataResultsIndexReader()
                    .Read(htmlDocument)
                    .Select(link => "https://www.racingpost.com" + link)
                    .Distinct()
                    .ToArray();
            }
            catch (ValidationException e)
            {
                throw new ValidationException($"Unexpected error getting links from {resultsUrl}: {e.Message}");
            }

            EnsureRacesWereFound(currentDate, resultsUrl, urls.Length);

            foreach (var url in urls)
            {
                yield return url;
            }

            currentDate = currentDate.AddDays(1);
        }
    }

    // The index renders the same "no results for this date" empty state whether a day genuinely had no
    // racing or its own data failed to load, so only the calendar can tell the two apart.
    private static void EnsureRacesWereFound(DateOnly date, string resultsUrl, int raceCount)
    {
        if (raceCount > 0 || IsExpectedBlankRacingDay(date))
        {
            return;
        }

        throw new ValidationException(
            $"Found no races at {resultsUrl}. Racing is expected on every date except Christmas Day, " +
            "so the results index did not render its races. Re-running will retry the day.");
    }

    private static bool IsExpectedBlankRacingDay(DateOnly date) => date is { Month: 12, Day: 25 };

    public async Task<RaceResult> DownloadResults(string url)
    {
        var htmlResponse = await htmlLoader.GetHtmlResponseFrom(url);
        return new NextDataRaceResultReader().Read(htmlResponse);
    }

    private async Task<HtmlDocument> GetHtmlDocumentFrom(string url)
    {
        var responseBody = await htmlLoader.GetHtmlResponseFrom(url);
        var htmlDocument = new HtmlDocument();
        htmlDocument.LoadHtml(responseBody);
        return htmlDocument;
    }

    public async IAsyncEnumerable<string> GetRaceCardUrls(DateOnly start, DateOnly end)
    {
        var currentDate = start;
        while (currentDate <= end)
        {
            var currentDateAsString = GetRaceCardDateAsString(currentDate);
            var resultsUrl = $"https://www.racingpost.com/racecards/time-order/{currentDateAsString}";
            HtmlDocument htmlDocument;
            try
            {
                htmlDocument = await GetHtmlDocumentFrom(resultsUrl);
            }
            catch (Exception e)
            {
                throw new Exception($"Failed to load URL {resultsUrl}: {e.Message}", e);
            }

            var finder = new HtmlNodeFinder(htmlDocument.DocumentNode);
            var urls =
                finder.Anchor()
                    .WithTestIdStartingWith("Link__TimeOrderRace__")
                    .GetNodes()
                    .Select(n => "https://www.racingpost.com" + n.GetAttributeValue("href", string.Empty))
                    .Distinct()
                    .ToArray();

            foreach (var url in urls)
            {
                yield return url;
            }

            currentDate = currentDate.AddDays(1);
        }
    }

    private string GetRaceCardDateAsString(DateOnly date)
    {
        if (clock.IsToday(date))
        {
            return string.Empty;
        }

        if (clock.IsTomorrow(date))
        {
            return "tomorrow";
        }

        return $"{date:yyyy-MM-dd}";
    }

    public async Task<RaceCard> DownloadRaceCard(string url)
    {
        var htmlResponse = await htmlLoader.GetHtmlResponseFrom(url);
        var parser = new RaceCardParser();
        return await parser.Parse(htmlResponse);
    }
}
