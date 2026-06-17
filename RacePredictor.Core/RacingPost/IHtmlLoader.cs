namespace RacePredictor.Core.RacingPost;

public interface IHtmlLoader
{
    public Task<string> GetHtmlResponseFrom(string url);
}
