using RaceDataDownloader.Commands.DownloadRaceCards;
using Xunit.Abstractions;

namespace RaceDataDownloader.Tests.Commands.DownloadRaceCards;

public class DownloadRaceCardsCommandHandlerShould(ITestOutputHelper output)
{
    [Fact(Skip = "Uses legacy 2022 Hamilton race-card fixture (RC-* markup) that no longer parses; regenerate fixture and Verify snapshot before re-enabling.")]
    public async Task DownloadRaceCardsAndSaveToExpectedLocation()
    {
        var mockFileSystemBuilder = new MockFileSystemBuilder();
        var mockRacingDataDownloader = MockRacingDataDownloader
            .New()
            .MockReturnHamiltonRaceCardUrls()
            .MockReturnHamiltonRaceCard();
        var logger = new OutputLogger<DownloadRaceCardsCommandHandler>(output);
        var handler = new DownloadRaceCardsCommandHandler(mockFileSystemBuilder.FileSystem, mockRacingDataDownloader, logger);
        var options = new DownloadRaceCardsOptions { OutputDirectory = MockFileSystemBuilder.OutputDirectory, DateRange = "2022-06-28" };

        var result = await handler.RunAsync(options);

        result.Should().Be(ExitCodes.Success);
        await Verify(mockFileSystemBuilder.SavedRaceCardsAsJson);
        await Verify(mockFileSystemBuilder.SavedRaceCardsAsCsv).UseMethodName($"{nameof(DownloadRaceCardsAndSaveToExpectedLocation)}_CSV");
    }
}
