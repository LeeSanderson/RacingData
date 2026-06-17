using System.Globalization;
using System.IO.Abstractions;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Serialization;
using CsvHelper;
using CsvHelper.Configuration;
using CsvHelper.Configuration.Attributes;
using ValidationException = System.ComponentModel.DataAnnotations.ValidationException;

namespace RaceDataDownloader.Commands;

public static class FileSystemExtensions
{
    private static readonly JsonSerializerOptions JsonSerializerOptions = new()
    {
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        IgnoreReadOnlyProperties = false,
        WriteIndented = true,
        Converters = { new JsonStringEnumConverter() }
    };

    // ReSharper disable once UnusedParameter.Global
#pragma warning disable IDE0060
    public static string GetResultsFileName(this IFileSystem fileSystem, string dataFolder, DateOnly date) =>
#pragma warning restore IDE0060
        Path.Combine(dataFolder, $"Results_{date.Year}{date.Month:00}.csv");

    // ReSharper disable once UnusedParameter.Global
#pragma warning disable IDE0060
    public static string GetPredictionScoresFileName(this IFileSystem fileSystem, string dataFolder, DateOnly date) =>
#pragma warning restore IDE0060
        Path.Combine(dataFolder, $"PredictionScores_{date.Year}{date.Month:00}.csv");

    public static async Task WriteRecordsToCsvFile<TRecord>(
        this IFileSystem fileSystem,
        string fileName,
        IEnumerable<TRecord> records)
    {
        fileSystem.DeleteFileIfExists(fileName);
        var csvString = await records.ToCsvString();
        await fileSystem.File.WriteAllTextAsync(fileName, csvString);
    }

    public static async Task<string> ToCsvString<TRecord>(this IEnumerable<TRecord> records)
    {
        await using var writer = new StringWriter();
        await using var csvWriter = new CsvWriter(writer, CultureInfo.InvariantCulture);
        await csvWriter.WriteRecordsAsync(records);
        return writer.ToString();
    }

    public static async Task<List<TRecord>> ReadRecordsFromCsvFile<TRecord>(
        this IFileSystem fileSystem,
        string fileName)
    {
        fileSystem.EnsureFileExists(fileName);
        var csvString = await fileSystem.File.ReadAllTextAsync(fileName);
        return await csvString.FromCsvString<TRecord>();
    }

    public static async Task<List<TRecord>> FromCsvString<TRecord>(this string data)
    {
        using var reader = new StringReader(data);
        using var csvReader = new CsvReader(reader, CreateReaderConfiguration<TRecord>());
        return await csvReader.GetRecordsAsync<TRecord>().ToListAsync();
    }

    private static CsvConfiguration CreateReaderConfiguration<TRecord>()
    {
        var configuration = new CsvConfiguration(CultureInfo.InvariantCulture);

        // CsvHelper honours [Optional] for name-mapped members but still throws
        // MissingFieldException for [Index]-mapped members whose column is absent
        // (e.g. a legacy Results_YYYYMM.csv written before the Forecast* columns existed).
        // Tolerate exactly those optional + indexed columns while keeping every other
        // column strict, so a genuinely truncated/malformed file still fails fast.
        var optionalIndexes = typeof(TRecord)
            .GetProperties()
            .Where(p => p.GetCustomAttribute<OptionalAttribute>() != null
                        && p.GetCustomAttribute<IndexAttribute>() != null)
            .Select(p => p.GetCustomAttribute<IndexAttribute>()!.Index)
            .ToHashSet();

        if (optionalIndexes.Count > 0)
        {
            var defaultHandler = configuration.MissingFieldFound;
            configuration.MissingFieldFound = args =>
            {
                if (optionalIndexes.Contains(args.Index))
                {
                    return;
                }

                defaultHandler?.Invoke(args);
            };
        }

        return configuration;
    }

    public static async Task WriteRecordsToJsonFile<TRecord>(this IFileSystem fileSystem, string outputFileName, List<TRecord> records)
    {
        fileSystem.DeleteFileIfExists(outputFileName);
        var jsonString = records.ToJsonString();
        await fileSystem.File.WriteAllTextAsync(outputFileName, jsonString);
    }

    public static string ToJsonString<TRecord>(this IEnumerable<TRecord> records) => JsonSerializer.Serialize(records, JsonSerializerOptions);

    public static async Task<List<TRecord>> ReadRecordsFromJsonFile<TRecord>(
        this IFileSystem fileSystem,
        string fileName)
    {
        fileSystem.EnsureFileExists(fileName);
        var jsonString = await fileSystem.File.ReadAllTextAsync(fileName);
        return JsonSerializer.Deserialize<List<TRecord>>(jsonString!) ?? [];
    }

    public static void DeleteFileIfExists(this IFileSystem fileSystem, string fileName)
    {
        if (fileSystem.File.Exists(fileName))
        {
            fileSystem.File.Delete(fileName);
            if (fileSystem.File.Exists(fileName))
            {
                throw new ValidationException($"Unable to delete existing file {fileName}");
            }
        }
    }

    public static void EnsureFileExists(this IFileSystem fileSystem, string fileName)
    {
        if (!fileSystem.File.Exists(fileName))
        {
            throw new ValidationException($"Unable to find expected file {fileName}");
        }
    }

    public static void CreateDirectoryIfNotExists(this IFileSystem fileSystem, string directory)
    {
        if (!fileSystem.Directory.Exists(directory))
        {
            fileSystem.Directory.CreateDirectory(directory);
            if (!fileSystem.Directory.Exists(directory))
            {
                throw new ValidationException($"Unable to create 'output' directory '{directory}' ");
            }
        }
    }

}
