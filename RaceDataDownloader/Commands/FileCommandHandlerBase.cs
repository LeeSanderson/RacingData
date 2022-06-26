using System.ComponentModel.DataAnnotations;
using System.IO.Abstractions;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace RaceDataDownloader.Commands;

public class FileCommandHandlerBase
{
    protected readonly IFileSystem FileSystem;

    public FileCommandHandlerBase(IFileSystem fileSystem)
    {
        FileSystem = fileSystem;
    }

    protected void DeleteFileIfExists(string fileName)
    {
        if (FileSystem.File.Exists(fileName))
        {
            FileSystem.File.Delete(fileName);
            if (FileSystem.File.Exists(fileName))
            {
                throw new ValidationException($"Unable to delete existing file {fileName}");
            }
        }
    }

    protected async Task SaveDataAsJson<TRecord>(string outputFileName, List<TRecord> records)
    {
        DeleteFileIfExists(outputFileName);

        var jsonString = JsonSerializer.Serialize(records,
            new JsonSerializerOptions
            {
                DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
                IgnoreReadOnlyProperties = false,
                WriteIndented = true,
                Converters = { new JsonStringEnumConverter() }
            });

        await FileSystem.File.WriteAllTextAsync(outputFileName, jsonString);
    }
    protected void CreateDirectoryIfNotExists(string directory)
    {
        if (!FileSystem.Directory.Exists(directory))
        {
            FileSystem.Directory.CreateDirectory(directory);
            if (!FileSystem.Directory.Exists(directory))
            {
                throw new ValidationException($"Unable to create 'output' directory '{directory}' ");
            }
        }
    }
}