using System.IO.Abstractions;
using System.Text.Json;
using NSubstitute;
using RaceDataDownloader.Commands;
using RaceDataDownloader.Commands.PredictTodaysRaceCards;
using RaceDataDownloader.Models;
using Xunit.Abstractions;

namespace RaceDataDownloader.Tests.Commands.PredictTodaysRaceCards;

public class PredictTodaysRaceCardsCommandHandlerShould
{
    private const string MockDataDirectory = @"c:\out";
    private const string TodaysRaceCard = @"c:\out\TodaysRaceCards.csv";
    private const string PredictionsFile = @"c:\out\Predictions.json";

    private readonly ITestOutputHelper _output;
    private readonly IFileSystem _mockFileSystem;

    private readonly List<RaceCardRecord> _raceCardForRaceBetweenHorse1AndHorse2 = new()
    {
        new RaceCardRecord
        {
            RaceId = 1,
            RaceName = "Race1",
            CourseId = 1,
            CourseName = "Course1",
            HorseId = 1,
            HorseName = "Horse1",
            Off = new DateTime(2022, 05, 13, 13, 40, 0),
            RacingPostRating = 100
        },
        new RaceCardRecord
        {
            RaceId = 1,
            RaceName = "Race1",
            CourseId = 1,
            CourseName = "Course1",
            HorseId = 2,
            HorseName = "Horse2",
            RacingPostRating = 99
        }
    };

    private readonly List<RaceCardPrediction> _predictionThatHorse1WillWin = new()
    {
        new RaceCardPrediction
        {
            RaceId = 1,
            RaceName = "Race1",
            CourseId = 1,
            CourseName = "Course1",
            HorseId = 1,
            HorseName = "Horse1",
            Off = new DateTime(2022, 05, 13, 13, 40, 0),
        }
    };

    public PredictTodaysRaceCardsCommandHandlerShould(ITestOutputHelper output)
    {
        _output = output;
        _mockFileSystem = Substitute.For<IFileSystem>();
    }

    [Fact]
    public async Task PredictHorse1WillWinWhenHorse1IsFasterThanHorse2()
    {
        _mockFileSystem.Directory.Exists(MockDataDirectory).Returns(true);
        string? savedPredictionsAsJson = null;
        _mockFileSystem.File.WriteAllTextAsync(PredictionsFile, Arg.Do<string>(x => savedPredictionsAsJson = x))
            .Returns(Task.CompletedTask);
        _mockFileSystem.File.ReadAllTextAsync(TodaysRaceCard).Returns(Task.FromResult(await _raceCardForRaceBetweenHorse1AndHorse2.ToCsvString()));
        _mockFileSystem.File.Exists(TodaysRaceCard).Returns(true);

        var logger = new OutputLogger<PredictTodaysRaceCardsCommandHandler>(_output);

        var handler = new PredictTodaysRaceCardsCommandHandler(_mockFileSystem, logger);
        var result = await handler.RunAsync(new PredictTodaysRaceCardsOptions { DataDirectory = MockDataDirectory });

        result.Should().Be(ExitCodes.Success);
        var generatedPredictions = JsonSerializer.Deserialize<List<RaceCardPrediction>>(savedPredictionsAsJson!);

        generatedPredictions.Should().BeEquivalentTo(_predictionThatHorse1WillWin);
    }
}