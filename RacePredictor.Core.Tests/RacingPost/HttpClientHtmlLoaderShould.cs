using System.Net;
using NSubstitute;
using RacePredictor.Core.RacingPost;
using RichardSzalay.MockHttp;

namespace RacePredictor.Core.Tests.RacingPost;

public class HttpClientHtmlLoaderShould
{
    private const string RaceResultsUrl = "https://www.racingpost.com/results/2022-05-11";

    [Fact]
    public async Task ReturnExpectedHtml()
    {
        var expectedHtml = ResourceLoader.ReadRacingPostExampleResource("daily_results_20220511.html");
        var mockHttpMessageHandler = new MockHttpMessageHandler();
        mockHttpMessageHandler
            .When(HttpMethod.Get, RaceResultsUrl)
            .Respond("text/html", expectedHtml);
        var htmlLoader = CreateHttpClientHtmlLoader(mockHttpMessageHandler);

        var actualHtml = await htmlLoader.GetHtmlResponseFrom(RaceResultsUrl);

        actualHtml.Should().Be(expectedHtml);
    }

    [Fact]
    public async Task FailWhenUnexpectedErrorEncountered()
    {
        var mockHttpMessageHandler = new MockHttpMessageHandler();
        mockHttpMessageHandler
            .When(HttpMethod.Get, RaceResultsUrl)
            .Respond(HttpStatusCode.InternalServerError);
        var htmlLoader = CreateHttpClientHtmlLoader(mockHttpMessageHandler);

        await Assert.ThrowsAsync<HttpRequestException>(() => htmlLoader.GetHtmlResponseFrom(RaceResultsUrl));
    }

    private static HttpClientHtmlLoader CreateHttpClientHtmlLoader(MockHttpMessageHandler mockHttpMessageHandler)
    {
        var httpClientFactory = Substitute.For<IHttpClientFactory>();
        httpClientFactory.CreateClient(Arg.Any<string>()).Returns(new HttpClient(mockHttpMessageHandler));

        return new HttpClientHtmlLoader(httpClientFactory);
    }
}
