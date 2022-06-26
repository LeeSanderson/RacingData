using CommandLine;

namespace RaceDataDownloader.Commands.DownloadResults;

[Verb("results", isDefault: true, HelpText = "Download race results")]
// ReSharper disable once ClassNeverInstantiated.Global - created implicitly in main program code.
public class DownloadResultsOptions
{
    [Option(
        'o',
        "output",
        Required = true,
        HelpText = "The directory to write the results to.")]
    public string? OutputDirectory { get; set; }

    [Option(
        'd',
        "dates",
        Required = true,
        HelpText = "A date (e.g. 2020-01-21) or date range (e.g. 2020-01-21-2020-01-28) to specify the days to get data for.")]
    public string? DateRange { get; set; }
}