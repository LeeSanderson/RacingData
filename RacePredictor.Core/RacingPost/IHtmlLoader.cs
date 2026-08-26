namespace RacePredictor.Core.RacingPost;

public interface IHtmlLoader
{
    /// <summary>
    /// Returns the page body at <paramref name="url"/>. A non-success response throws
    /// <see cref="HttpRequestException"/> carrying its <see cref="HttpRequestException.StatusCode"/>, so
    /// callers can tell a missing page (404) from a failure worth aborting the whole download for.
    /// </summary>
    public Task<string> GetHtmlResponseFrom(string url);
}
