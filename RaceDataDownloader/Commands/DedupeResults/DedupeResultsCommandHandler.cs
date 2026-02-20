using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using RaceDataDownloader.Models;

namespace RaceDataDownloader.Commands.DedupeResults;

public class DedupeResultsCommandHandler(IFileSystem fileSystem, ILogger<DedupeResultsCommandHandler> logger)
    : FileCommandHandlerBase<DedupeResultsCommandHandler, DedupeResultsOptions>(fileSystem, logger)
{
    protected override async Task InternalRunAsync(DedupeResultsOptions options)
    {
        var dataFolder = ValidateAndCreateOutputFolder(options.DataDirectory);
        foreach (var fileName in FileSystem.Directory.EnumerateFiles(dataFolder, "Results_*.csv"))
        {
            var raceResults = await FileSystem.ReadRecordsFromCsvFile<RaceResultRecord>(fileName);
            var deDupedRaceResults = new List<RaceResultRecord>();
            foreach (var raceResult in raceResults)
            {
                if (!deDupedRaceResults.Contains(raceResult))
                {
                    deDupedRaceResults.Add(raceResult);
                }
            }

            Logger.LogInformation(
                "Deduped {FileName}. {Duplicates} duplicates found",
                fileName,
                raceResults.Count - deDupedRaceResults.Count);
            if (deDupedRaceResults.Count < raceResults.Count)
            {
                await FileSystem.File.WriteAllTextAsync(fileName, await deDupedRaceResults.ToCsvString());
            }
        }
    }
}
