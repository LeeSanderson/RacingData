namespace RacePredictor.Core.RacingPost;

public interface IRacingDataDownloader
{
    public IAsyncEnumerable<string> GetResultUrls(DateOnly start, DateOnly end);
    public Task<RaceResult> DownloadResults(string url);
    public IAsyncEnumerable<string> GetRaceCardUrls(DateOnly start, DateOnly end);
    public Task<RaceCard> DownloadRaceCard(string url);
}
