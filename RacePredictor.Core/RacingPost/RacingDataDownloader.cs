using System.Net;
using HtmlAgilityPack;

namespace RacePredictor.Core.RacingPost;

public class RacingDataDownloader
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly IClock _clock;

    public RacingDataDownloader(IHttpClientFactory httpClientFactory, IClock clock)
    {
        _httpClientFactory = httpClientFactory;
        _clock = clock;
    }

    public async IAsyncEnumerable<string> GetResultUrls(DateOnly start, DateOnly end)
    {
        var currentDate = start;
        while (currentDate <= end)
        {
            var resultsUrl = $"https://www.racingpost.com/results/{currentDate:yyyy-MM-dd}";
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
            HtmlNode[] linkNodes = [];
            try
            {
                linkNodes = finder.Anchor()
                    .WithSelector("link-listCourseNameLink")
                    .GetNodes();
            }
            catch
            {
                // This may fail if there are no races for a given day (e.g. Christmas Day)
                // Verify this is the case by trying to get an optional "No results found" node 
                var errorMessage = finder.Optional().Div().WithSelector("text-errorMessageText").GetText();
                if (errorMessage != "No results in the Racing Post records for this date")
                {
                    throw new Exception($"Unexpected error getting links from {resultsUrl}: {errorMessage}");
                }
            }

            var urls = linkNodes
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

    public async Task<RaceResult> DownloadResults(string url)
    {
        var htmlResponse = await GetHtmlResponseFrom(url);
        var parser = new RacingResultParser();
        return await parser.Parse(htmlResponse);
    }

    private async Task<string> GetHtmlResponseFrom(string url)
    {
        const int maxAttempts = 7;
        const int delayMilliseconds = 1700;

        var client = _httpClientFactory.CreateClient();

        HttpClientHelper.ConfigureRandomHeader(client);

        HttpResponseMessage? response = null;
        for (var attempt = 0; attempt <= maxAttempts; attempt++)
        {
            response = await client.GetAsync(url);
            if (response.StatusCode == HttpStatusCode.NotAcceptable)
            {
                if (attempt < maxAttempts)
                {
                    // Retry after delay
                    await Task.Delay(delayMilliseconds);
                }
                else
                {
                    throw new Exception($"Received 406 for {maxAttempts} attempts on {url}");
                }
            }
            else
            {
                break;
            }
        }

        response!.EnsureSuccessStatusCode();
        return await response.Content.ReadAsStringAsync();
    }

    private async Task<HtmlDocument> GetHtmlDocumentFrom(string url)
    {
        var responseBody = await GetHtmlResponseFrom(url);
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
            var resultsUrl = $"https://www.racingpost.com/racecards/{currentDateAsString}";
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
                    .WithCssClass("RC-meetingItem__link")
                    .GetNodes()
                    .Select(n => "https://www.racingpost.com" + n.GetAttributeValue("href", string.Empty))
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
        if (_clock.IsToday(date))
        {
            return string.Empty;
        }

        if (_clock.IsTomorrow(date))
        {
            return "tomorrow";
        }

        return $"{date:yyyy-MM-dd}";
    }

    public async Task<RaceCard> DownloadRaceCard(string url)
    {
        var htmlResponse = await GetHtmlResponseFrom(url);
        var parser = new RaceCardParser();
        return await parser.Parse(htmlResponse);
    }
}
