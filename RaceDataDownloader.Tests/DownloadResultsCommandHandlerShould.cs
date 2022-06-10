using System.IO.Abstractions;
using NSubstitute;
using RaceDataDownloader.Tests.Fakes;
using RichardSzalay.MockHttp;
using Xunit.Abstractions;

namespace RaceDataDownloader.Tests
{
    [UsesVerify]
    public class DownloadResultsCommandHandlerShould
    {
        private readonly ITestOutputHelper _output;

        public DownloadResultsCommandHandlerShould(ITestOutputHelper output)
        {
            _output = output;
        }

        [Fact]
        public async Task DownloadResultsAndSaveToExpectedLocation()
        {
            var mockFileSystem = Substitute.For<IFileSystem>();
            string? savedResultsJson = null;
            mockFileSystem.File.WriteAllTextAsync(@"c:\out\Results.json", Arg.Do<string>(x => savedResultsJson = x))
                .Returns(Task.CompletedTask);
            mockFileSystem.Directory.Exists(@"c:\out").Returns(true);

            var mockHttpMessageHandler = new MockHttpMessageHandler();
            mockHttpMessageHandler.When(HttpMethod.Get, "https://www.racingpost.com/results/2022-05-11")
                .Respond("text/html", FakeData.DailyResultsFor20220511);
            mockHttpMessageHandler.When(HttpMethod.Get, "https://www.racingpost.com/results/5/bath/2022-05-11/809925")
                .Respond("text/html", FakeData.BathRaceResultFor1730RaceOn20220511);

            var httpClientFactory = Substitute.For<IHttpClientFactory>();
            httpClientFactory.CreateClient(Arg.Any<string>()).Returns(new HttpClient(mockHttpMessageHandler));
            var logger = new OutputLogger<DownloadResultsCommandHandler>(_output);

            var handler = new DownloadResultsCommandHandler(mockFileSystem, httpClientFactory,logger);
            var result = await handler.RunAsync(new DownloadResultsOptions { OutputDirectory = @"c:\out", DateRange = "2022-05-11" });

            result.Should().Be(0);
            await Verify(savedResultsJson);
        }
    }
}