using CommandLine;

namespace RaceDataDownloader.Commands.UpdateResults;

[Verb("updateresults", HelpText = "Ensure we have race results for a given period of time (separating results into monthly CSV files)")]
public class UpdateResultsOptions
{
    public const int DefaultMinimumPeriodInDays = 120;

    [Option(
        'o',
        "output",
        Required = true,
        HelpText = "The directory to store result data.")]
    public string? DataDirectory { get; set; }

    [Option(
        'p',
        "period",
        Required = false,
        Default = 120,
        HelpText = "The number of days of data to maintain. The command ensures that data for a least the specified number of days exists.")]
    public int MinimumPeriodInDays { get; set; } = DefaultMinimumPeriodInDays;
}