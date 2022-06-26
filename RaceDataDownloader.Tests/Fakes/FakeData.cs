using System.Reflection;

namespace RaceDataDownloader.Tests.Fakes;

internal static class FakeData
{
    public static string DailyResultsFor20220511 => ReadResource("FakeResultsPage.html");
    public static string BathRaceResultFor1730RaceOn20220511 => ReadResource("Bath_Results_20220511_1730.html");
    public static string DailyRaceCardsFor20220628 => ReadResource("FakeRaceCardsPage.html");
    public static string HamiltonRacecardFor1315RaceOn20220628 => ReadResource("Hamilton_RaceCard_20220628_1315.html");

    private static string ReadResource(string fileName)
    {
        var assembly = Assembly.GetExecutingAssembly();

        var resourceName = $"{typeof(FakeData).Namespace}.{fileName}";

        using var stream = assembly.GetManifestResourceStream(resourceName);
        if (stream == null)
            throw new Exception($"Resource {fileName} not found");

        using var reader = new StreamReader(stream);
        return reader.ReadToEnd();
    }
}