using CommandLine;

namespace RaceDataDownloader.Commands.DedupeResults;

[Verb("deduperesults", HelpText = "De-dupe all race results files in a given directory")]
public class DedupeResultsOptions
{
    [Option(
        'o',
        "output",
        Required = true,
        HelpText = "The directory to store/update result data.")]
    public string? DataDirectory { get; set; }
}