using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using RaceDataDownloader.Models;

namespace RaceDataDownloader.Commands.FixRaceIds;

public class FixRaceIdsCommandHandler(IFileSystem fileSystem, ILogger<FixRaceIdsCommandHandler> logger)
    : FileCommandHandlerBase<FixRaceIdsCommandHandler, FixRaceIdsOptions>(fileSystem, logger)
{
    protected override async Task InternalRunAsync(FixRaceIdsOptions options)
    {
        var dataFolder = ValidateAndCreateOutputFolder(options.DataDirectory);
        foreach (var fileName in FileSystem.Directory.EnumerateFiles(dataFolder, "Results_*.csv"))
        {
            var raceResults = await FileSystem.ReadRecordsFromCsvFile<RaceResultRecord>(fileName);
            var fixedRecords = 0;

            foreach (var raceResult in raceResults)
            {
                if (raceResult.RaceId == raceResult.CourseId)
                {
                    raceResult.RaceId = GenerateUniqueIdFromOff(raceResult.Off);
                    fixedRecords++;
                }
            }

            Logger.LogInformation(
                "Fixed RaceIds in {FileName}. {FixedRecords} ids fixed",
                fileName,
                fixedRecords);
            if (fixedRecords > 0)
            {
                await FileSystem.File.WriteAllTextAsync(fileName, await raceResults.ToCsvString());
            }
        }
    }

    private static int GenerateUniqueIdFromOff(DateTime off)
    {
        // Convert time to minutes since epoch, which should be unique enough for our purposes and is more compact than using seconds
        var utcOff = DateTime.SpecifyKind(off, DateTimeKind.Utc);
        return (int)new DateTimeOffset(utcOff).ToUnixTimeSeconds() / 60;
    }
}
