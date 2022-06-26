using HtmlAgilityPack;

namespace RacePredictor.Core.RacingPost;

public class RacingDataDownloader
{
    private readonly IHttpClientFactory _httpClientFactory;

    public RacingDataDownloader(IHttpClientFactory httpClientFactory)
    {
        _httpClientFactory = httpClientFactory;
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
            var urls =
                finder.Anchor()
                    .WithSelector("link-listCourseNameLink")
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

    public async Task<RaceResult> DownloadResults(string url)
    {
        var htmlResponse = await GetHtmlResponseFrom(url);
        var parser = new RacingResultParser();
        return await parser.Parse(htmlResponse);
    }

    private async Task<string> GetHtmlResponseFrom(string url)
    {
        var client = _httpClientFactory.CreateClient();
        HttpClientHelper.ConfigureRandomHeader(client);
        var response = await client.GetAsync(url);
        response.EnsureSuccessStatusCode();
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
            var resultsUrl = $"https://www.racingpost.com/racecards/{currentDate:yyyy-MM-dd}";
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
}