using System.Net;
using Microsoft.Extensions.Logging;
using RacePredictor.Core;
using RacePredictor.Core.RacingPost;

namespace RaceDataDownloader.Commands
{
    internal static class RacingDataDownloaderExtensions
    {
        public static async Task<List<RaceCard>> DownloadRaceCardsInDateRange(
            this RacingDataDownloader downloader, ILogger logger, DateOnly start, DateOnly end)
        {
            var raceResults = new List<RaceCard>();
            await foreach (var url in downloader.GetRaceCardUrls(start, end))
            {
                logger.LogInformation("Attempting to load race card from {URL}", url);
                try
                {
                    var raceResult = await downloader.DownloadRaceCard(url);
                    raceResults.Add(raceResult);
                }
                catch (HttpRequestException hre)
                {
                    if (hre.StatusCode == HttpStatusCode.NotFound)
                    {
                        logger.LogInformation("Skipping {URL} - could not find race card (404)", url);
                    }
                    else
                    {
                        throw;
                    }
                }
            }

            return raceResults;
        }

    }
}
