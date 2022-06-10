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
        var client = _httpClientFactory.CreateClient();
        var currentDate = start;
        while (currentDate <= end)
        {
            var resultsUrl = $"https://www.racingpost.com/results/{currentDate:yyyy-MM-dd}";
            string responseBody;
            try
            {
                var response = await client.GetAsync(resultsUrl);
                response.EnsureSuccessStatusCode();
                responseBody = await response.Content.ReadAsStringAsync();
            }
            catch (Exception e)
            {
                throw new Exception($"Failed to load URL {resultsUrl}: {e.Message}", e);
            }

            var htmlDocument = new HtmlDocument();
            htmlDocument.LoadHtml(responseBody);
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
}