using System.ComponentModel.DataAnnotations;
using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using RacePredictor.Core;

namespace RaceDataDownloader.Commands;

public abstract class FileCommandHandlerBase<TCommandHandler, TOptions>
    where TCommandHandler : FileCommandHandlerBase<TCommandHandler, TOptions>
{
    protected readonly IFileSystem FileSystem;
    protected readonly ILogger<TCommandHandler> Logger;

    protected FileCommandHandlerBase(IFileSystem fileSystem, ILogger<TCommandHandler> logger)
    {
        FileSystem = fileSystem;
        Logger = logger;
    }

    public async Task<int> RunAsync(TOptions options)
    {
        try
        {
            await InternalRunAsync(options);
        }
        catch (ValidationException ve)
        {
            Logger.LogError(ve.Message);
            return ExitCodes.Error;
        }
        catch (Exception e)
        {
            Logger.LogError(e, "{Handler} failed with unexpected error", GetType());
            return ExitCodes.Error;
        }

        return ExitCodes.Success;

    }

    protected abstract Task InternalRunAsync(TOptions options);

    protected string ValidateAndCreateOutputFolder(string? possibleOutputDirectory)
    {
        var outputFolder = possibleOutputDirectory ??
                           throw new ValidationException("Required 'output' parameter was not provided.");
        FileSystem.CreateDirectoryIfNotExists(outputFolder);
        return outputFolder;
    }

    protected static (DateOnly start, DateOnly end) ValidateAndParseDateRange(string? dateRange)
    {
        var range = dateRange ?? throw new ValidationException("Required 'dates' parameter was not provided.");
        try
        {
            return range.ToRange();
        }
        catch (Exception e)
        {
            throw new ValidationException(e.Message);
        }
    }
}