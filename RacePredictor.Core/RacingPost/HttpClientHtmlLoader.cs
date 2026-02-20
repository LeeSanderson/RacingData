using System.Net;

namespace RacePredictor.Core.RacingPost;

public class HttpClientHtmlLoader(IHttpClientFactory httpClientFactory) : IHtmlLoader
{
    public async Task<string> GetHtmlResponseFrom(string url)
    {
        const int maxAttempts = 7;
        const int delayMilliseconds = 1700;

        var client = httpClientFactory.CreateClient();

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
}
