using CommandLine;

namespace RaceDataDownloader.Commands.PredictTodaysRaceCards;

[Verb("predict", HelpText = "Generate a 'Predictions.json' file by comparing the 'TodaysRaceCards.csv' to the available race results")]
public class PredictTodaysRaceCardsOptions
{
    [Option(
        'o',
        "output",
        Required = true,
        HelpText = "The directory to read the data from and store the 'Predictions.json' file.")]
    public string? DataDirectory { get; set; }
}