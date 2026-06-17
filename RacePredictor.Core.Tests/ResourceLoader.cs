using System.Globalization;
using System.Reflection;
using CsvHelper;

namespace RacePredictor.Core.Tests;

internal static class ResourceLoader
{
    internal static string ReadRacingPostExampleResource(string fileName) =>
        ReadResource($"{typeof(ResourceLoader).Namespace}.RacingPost.Examples.{fileName}");

    internal static async Task<List<TRecord>> ReadCsvResourceAs<TRecord>(string resourceName)
    {
        var data = ReadResource(resourceName);
        using var reader = new StringReader(data);
        using var csvReader = new CsvReader(reader, CultureInfo.InvariantCulture);
        return await csvReader.GetRecordsAsync<TRecord>().ToListAsync();
    }

    private static string ReadResource(string resourceName)
    {
        var assembly = Assembly.GetExecutingAssembly();

        using var stream = assembly.GetManifestResourceStream(resourceName) ?? throw new Exception($"Resource {resourceName} not found");

        using var reader = new StreamReader(stream);
        return reader.ReadToEnd();
    }
}
