using RaceDataDownloader.Commands.DownloadResults;
using Xunit.Abstractions;

namespace RaceDataDownloader.Tests.Commands.DownloadResults;

public class DownloadResultsCommandHandlerShould(ITestOutputHelper output)
{
    [Fact]
    public async Task DownloadResultsAndSaveToExpectedLocation()
    {
        var mockFileSystemBuilder = new MockFileSystemBuilder();
        var mockRacingDataDownloader = await MockRacingDataDownloader
            .New()
            .MockRaceResultUrls()
            .MockReturnBathRaceResults();
        var logger = new OutputLogger<DownloadResultsCommandHandler>(output);

        var handler = new DownloadResultsCommandHandler(mockFileSystemBuilder.FileSystem, mockRacingDataDownloader, logger);
        var options = new DownloadResultsOptions { OutputDirectory = MockFileSystemBuilder.OutputDirectory, DateRange = "2022-05-11" };
        var result = await handler.RunAsync(options);

        result.Should().Be(ExitCodes.Success);
        await Verify(mockFileSystemBuilder.SavedResultsAsJson);
        await Verify(mockFileSystemBuilder.SavedResultsAsCsv).UseMethodName($"{nameof(DownloadResultsAndSaveToExpectedLocation)}_CSV");
    }
}
