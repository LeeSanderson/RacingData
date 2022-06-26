using System.ComponentModel.DataAnnotations;
using System.IO.Abstractions;

namespace RaceDataDownloader;

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