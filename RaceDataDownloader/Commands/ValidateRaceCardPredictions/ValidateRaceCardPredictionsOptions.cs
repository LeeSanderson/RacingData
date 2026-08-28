using CommandLine;

namespace RaceDataDownloader.Commands.ValidateRaceCardPredictions;


[Verb("validate", HelpText = "Score 'TodaysPredictions.csv' by comparing to the available race results")]
public class ValidateRaceCardPredictionsOptions
{
    [Option(
        'o',
        "output",
        Required = true,
        HelpText = "The directory to read the 'TodaysPredictions.csv' file and store prediction scores.")]
    public string? DataDirectory { get; set; }
}