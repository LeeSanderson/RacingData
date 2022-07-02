using System.IO.Abstractions;

namespace RaceDataDownloader.Commands;

public class FileCommandHandlerBase
{
    protected readonly IFileSystem FileSystem;

    public FileCommandHandlerBase(IFileSystem fileSystem)
    {
        FileSystem = fileSystem;
    }
}