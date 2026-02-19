using CommandLine;

namespace RaceDataDownloader.Commands.FixRaceIds;

[Verb("fixraceids", HelpText = "Fix RaceId fields where the id matches the course id due to a bug.")]
public class FixRaceIdsOptions
{
    [Option(
        'o',
        "output",
        Required = true,
        HelpText = "The directory to store/update result data.")]
    public string? DataDirectory { get; set; }
}
