﻿using System.Globalization;
using System.IO.Abstractions;
using System.Text.Json;
using System.Text.Json.Serialization;
using CsvHelper;
using ValidationException = System.ComponentModel.DataAnnotations.ValidationException;

namespace RaceDataDownloader.Commands
{
    public static class FileSystemExtensions
    {
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
            using var reader = new StringReader(csvString);
            using var csvReader = new CsvReader(reader, CultureInfo.InvariantCulture);
            return await csvReader.GetRecordsAsync<TRecord>().ToListAsync();
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

        public static void EnsureFileExists(this IFileSystem fileSystem, string fileName)
        {
            if (!fileSystem.File.Exists(fileName))
            { 
                throw new ValidationException($"Unable to fine expected file {fileName}");
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