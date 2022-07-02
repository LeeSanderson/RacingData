using System.Globalization;
using System.IO.Abstractions;
using System.Text.Json;
using System.Text.Json.Serialization;
using CsvHelper;
using ValidationException = System.ComponentModel.DataAnnotations.ValidationException;

namespace RaceDataDownloader.Commands
{
    internal static class FileSystemExtensions
    {
        public static async Task WriteRecordsToCsvFile<TRecord>(
            this IFileSystem fileSystem,
            string fileName,
            IEnumerable<TRecord> records)
        {
            fileSystem.DeleteFileIfExists(fileName);

            await using var writer = new StringWriter();
            await using var csvWriter = new CsvWriter(writer, CultureInfo.InvariantCulture);

            await csvWriter.WriteRecordsAsync(records);

            var csvString = writer.ToString();
            await fileSystem.File.WriteAllTextAsync(fileName, csvString);
        }

        public static async Task<List<TRecord>> ReadRecordsFromCsvFile<TRecord>(
            this IFileSystem fileSystem,
            string fileName)
        {
            throw new NotImplementedException();
        }

        public static async Task WriteRecordsToJsonFile<TRecord>(this IFileSystem fileSystem, string outputFileName, List<TRecord> records)
        {
            fileSystem.DeleteFileIfExists(outputFileName);

            var jsonString = JsonSerializer.Serialize(records,
                new JsonSerializerOptions
                {
                    DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
                    IgnoreReadOnlyProperties = false,
                    WriteIndented = true,
                    Converters = { new JsonStringEnumConverter() }
                });

            await fileSystem.File.WriteAllTextAsync(outputFileName, jsonString);
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
}
