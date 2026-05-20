using System.Reflection;

namespace RaceDataDownloader.Tests.Fakes;

internal static class FakeData
{
    public static string BathRaceResultFor1730RaceOn20220511 => ReadResource("Bath_Results_20220511_1730.html");
    public static string HappyValleyRaceCardFor1140RaceOn20260520 => ReadResource("HappyValley_RaceCard_20260520_1140.html");

    private static string ReadResource(string fileName)
    {
        var assembly = Assembly.GetExecutingAssembly();

        var resourceName = $"{typeof(FakeData).Namespace}.{fileName}";

        using var stream = assembly.GetManifestResourceStream(resourceName) ?? throw new Exception($"Resource {fileName} not found");

        using var reader = new StreamReader(stream);
        return reader.ReadToEnd();
    }
}
