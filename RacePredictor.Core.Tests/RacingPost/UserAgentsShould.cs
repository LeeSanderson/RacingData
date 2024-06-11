using RacePredictor.Core.RacingPost;

namespace RacePredictor.Core.Tests.RacingPost;

public class UserAgentsShould
{
    [Fact]
    public void AllBeParseable()
    {
        var client = new HttpClient();
        var index = 0;
        foreach (var userAgent in UserAgents.Values)
        {
            client.DefaultRequestHeaders.UserAgent.Clear();
            try
            {
                client.DefaultRequestHeaders.UserAgent.ParseAdd(userAgent);
            }
            catch (Exception e)
            {
                Assert.True(false, $"Failed to parse user agent at position {index}: '{userAgent}' failed due to '{e.Message}'");
            }

            index++;
        }
    }
}
