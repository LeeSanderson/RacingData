using System;
using System.Net;
using Microsoft.Extensions.DependencyInjection;
using RacePredictor.Core.RacingPost;

namespace RacePredictor.Core.Tests.RacingPost;

public class IntegrationTests
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly CookieContainer _cookieContainer;

    public IntegrationTests()
    {
        var serviceCollection = new ServiceCollection();
        serviceCollection.AddSingleton<CookieContainer>();
        serviceCollection.AddHttpClient().ConfigureHttpClientDefaults(builder =>
        {
            builder.ConfigurePrimaryHttpMessageHandler(sp => new SocketsHttpHandler
            {
                UseCookies = true, CookieContainer = sp.GetRequiredService<CookieContainer>()
            });
        });
        var serviceProvider = serviceCollection.BuildServiceProvider();
        _httpClientFactory = serviceProvider.GetRequiredService<IHttpClientFactory>();
        _cookieContainer = serviceProvider.GetRequiredService<CookieContainer>();

        // Add a dummy token cookie to avoid 406 responses
        var uri = new Uri("https://www.racingpost.com");
        const string tokenName = "CognitoIdentityServiceProvider.3fii107m4bmtggnm21pud2es21.example%40gmail.com.accessToken";
        var tokenValue = $"ey{Guid.NewGuid():N}kxCRHN4RlFTT29PSWwyYzltK1ZyRUdRTjA4PSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiIxMjc1MzQxNC1jMDAxLTcwZDEtMmU2My03ZDM3NjhlYzYxZjEiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAuZXUtd2VzdC0xLmFtYXpvbmF3cy5jb21cL2V1LXdlc3QtMV9iQzBOenlpS2oiLCJjbGllbnRfaWQiOiIzZmlpMTA3bTRibXRnZ25tMjFwdWQyZXMyMSIsIm9yaWdpbl9qdGkiOiIzZTIwNjBkMi0xMDkwLTQyNjUtODhiYi1kMmNjYTNhMDZjYzciLCJldmVudF9pZCI6IjMyMzQ2YTg5LTk0YzktNGQ4Yy1hNTA4LTM3NjNiOTFjZDhkOSIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE3Njk1MjM0NjIsImV4cCI6MTc2OTUyNTI2MiwiaWF0IjoxNzY5NTIzNDYyLCJqdGkiOiJiMjE3ZTZiNC1hMTdhLTQzMGItODQ0Ni0xMWU5MmFmMTA0MjciLCJ1c2VybmFtZSI6IjEyNzUzNDE0LWMwMDEtNzBkMS0yZTYzLTdkMzc2OGVjNjFmMSJ9.D1q50MmumQerxmcpCcnCx0CA63gyIp1WN36DAeUAxTTOAGX23klwdAVEjYVOjgjZq0HwmBBgbqN6ohhd1vV18eCzCmGtljzRRiEamHO5TKygalIVRXyrrB67mD03vox0aIiLefb4A4Urr-HtJIYPChjczw9IVFnWZwgOM7k-gwkW8cGVs5qVO3czIKV8t8N53-aJhPO4qkQuJKQumJmI2_j6HMKt7Dj2h7avG3nfsNLHsD0dD_nwU6yg6JR5VH58GP48tf5wHsQrxal0viHzkNZufWDvgDiVnXrHyzjfu1-X6MDs1FpkeOSOUkn1PHKz6NYyC44Jf9G3Ts2XqXakbQ";
        _cookieContainer.Add(uri, new Cookie(tokenName, tokenValue));
    }

    // [Fact]
    public async Task RetrieveRacingResultsSuccessfully()
    {
        List<string> urls = [
            "https://www.racingpost.com/results/1138/dundalk-aw/2025-01-27/886906",
            "https://www.racingpost.com/results/1138/dundalk-aw/2025-01-27/886907",
            "https://www.racingpost.com/results/1138/dundalk-aw/2025-01-27/886906",
        ];
        foreach (var url in urls)
        {
            await GetHtmlResponseFrom("https://www.racingpost.com/results/1138/dundalk-aw/2025-01-27/886906");
        }
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

}
