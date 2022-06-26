using CommandLine;

namespace RaceDataDownloader.Commands.DownloadRaceCards;

[Verb("racecards", isDefault: true, HelpText = "Download race cards")]
public class DownloadRaceCardsOptions
{
    [Option(
        'o',
        "output",
        Required = true,
        HelpText = "The directory to write the race cards to.")]
    public string? OutputDirectory { get; set; }

    [Option(
        'd',
        "dates",
        Required = true,
        HelpText = "A date (e.g. 2020-01-21) or date range (e.g. 2020-01-21-2020-01-28) to specify the days to get data for.")]
    public string? DateRange { get; set; }
}