namespace RacePredictor.Core.RacingPost;

internal static class HttpClientHelper
{
    private static readonly string[] DoNotTrackOptions = { "0", "1" };
    private static readonly Random Random = new();

    public static void ConfigureRandomHeader(HttpClient client)
    {
        var headers = client.DefaultRequestHeaders;
        headers.Referrer = new Uri("https://www.google.com");
        headers.Add("Dnt", Choose(DoNotTrackOptions));
        headers.UserAgent.Clear();
        headers.UserAgent.ParseAdd(Choose(UserAgents.Values));
        headers.Add("X-Forwarded-For", RandomIpAddress());
        headers.Add("Upgrade-Insecure-Requests", "1");
    }

    private static string RandomIpAddress() =>
        $"{Random.Next(255)}:{Random.Next(255)}:{Random.Next(255)}:{Random.Next(255)}";

    private static string Choose(string[] option) => option[Random.Next(option.Length)];
}
