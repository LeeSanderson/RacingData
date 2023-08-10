using System.Reflection;

namespace RacePredictor.Core.Tests.RacingPost;

internal static class ResourceLoader
{
    internal static string ReadResource(string fileName)
    {
        var assembly = Assembly.GetExecutingAssembly();

        var resourceName = $"{typeof(ResourceLoader).Namespace}.Examples.{fileName}";

        using var stream = assembly.GetManifestResourceStream(resourceName) ?? throw new Exception($"Resource {fileName} not found");

        using var reader = new StreamReader(stream);
        return reader.ReadToEnd();
    }
}
