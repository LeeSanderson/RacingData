using CommandLine;

namespace RaceDataDownloader.Commands.DownloadTodaysRaceCards;

[Verb("todaysracecards", HelpText = "Download race cards for today")]
public class DownloadTodaysRaceCardsOptions
{
    [Option(
        'o',
        "output",
        Required = true,
        HelpText = "The directory to store race card data as 'TodaysRaceCards.csv'.")]
    public string? DataDirectory { get; set; }
}