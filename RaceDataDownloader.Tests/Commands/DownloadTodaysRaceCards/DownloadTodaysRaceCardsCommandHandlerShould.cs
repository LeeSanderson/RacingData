using System.IO.Abstractions;
using NSubstitute;
using RaceDataDownloader.Commands.DownloadTodaysRaceCards;
using RacePredictor.Core.RacingPost;
using Xunit.Abstractions;

namespace RaceDataDownloader.Tests.Commands.DownloadTodaysRaceCards;

public class DownloadTodaysRaceCardsCommandHandlerShould(ITestOutputHelper output)
{
    [Fact]
    public async Task DownloadRaceCardsAndSaveToExpectedLocation()
    {
        var mockFileSystemBuilder = new MockFileSystemBuilder();
        var mockRacingDataDownloader = MockRacingDataDownloader
            .New()
            .MockReturnHamiltonRaceCardUrls()
            .MockReturnHamiltonRaceCard();
        var clock = Substitute.For<IClock>();
        clock.Today.Returns(new DateOnly(2022, 06, 28));
        var logger = new OutputLogger<DownloadTodaysRaceCardsCommandHandler>(output);
        
        var handler = new DownloadTodaysRaceCardsCommandHandler(mockFileSystemBuilder.FileSystem, mockRacingDataDownloader, clock, logger);
        var options = new DownloadTodaysRaceCardsOptions { DataDirectory = MockFileSystemBuilder.OutputDirectory };
        var result = await handler.RunAsync(options);

        result.Should().Be(ExitCodes.Success);
        await Verify(mockFileSystemBuilder.TodaysSavedResultsAsCsv);
    }
}
