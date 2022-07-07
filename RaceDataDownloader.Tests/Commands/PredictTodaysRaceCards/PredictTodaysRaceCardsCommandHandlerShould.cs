using System.IO.Abstractions;
using System.Text.Json;
using NSubstitute;
using RaceDataDownloader.Commands;
using RaceDataDownloader.Commands.PredictTodaysRaceCards;
using RaceDataDownloader.Models;
using RacePredictor.Core;
using RacePredictor.Core.RacingPost;
using Xunit.Abstractions;

namespace RaceDataDownloader.Tests.Commands.PredictTodaysRaceCards;

public class PredictTodaysRaceCardsCommandHandlerShould
{
    private const string MockDataDirectory = @"c:\out";
    private const string ResultsFileForMay2022 = @"c:\out\Results_202205.csv";
    private const string TodaysRaceCard = @"c:\out\TodaysRaceCards.csv";
    private const string PredictionsFile = @"c:\out\Predictions.json";

    private readonly ITestOutputHelper _output;
    private readonly IFileSystem _mockFileSystem;
    private readonly List<RaceResultRecord> _resultsWhereHorse1IsFasterThanHorse2 = new()
    {
        new RaceResultRecord
        {
            HorseId = 1, 
            Off = new DateTime(2022, 05, 12, 13, 40, 0),
            RaceType = RaceType.Flat,
            DistanceInMeters = 3500,
            Going = "Good",
            RaceTimeInSeconds = 247.9
        },
        new RaceResultRecord
        {
            HorseId = 2, 
            Off = new DateTime(2022, 05, 12, 13, 40, 0), 
            RaceType = RaceType.Flat, 
            DistanceInMeters = 3500, 
            Going = "Good", 
            RaceTimeInSeconds = 300.9
        }
    };

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
            RaceType = RaceType.Flat,
            DistanceInMeters = 3500,
            Going = "Good"
        },
        new RaceCardRecord
        {
            RaceId = 1,
            RaceName = "Race1",
            CourseId = 1,
            CourseName = "Course1",
            HorseId = 2,
            HorseName = "Horse2",
            RaceType = RaceType.Flat,
            DistanceInMeters = 3500,
            Going = "Good"
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
        _mockFileSystem.File.ReadAllTextAsync(ResultsFileForMay2022).Returns(Task.FromResult(_resultsWhereHorse1IsFasterThanHorse2.ToCsvString().Result));
        _mockFileSystem.File.Exists(ResultsFileForMay2022).Returns(true);

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

        var clock = Substitute.For<IClock>();
        clock.Today.Returns(new DateOnly(2022, 05, 13));

        var logger = new OutputLogger<PredictTodaysRaceCardsCommandHandler>(_output);

        var handler = new PredictTodaysRaceCardsCommandHandler(_mockFileSystem, clock, logger);
        var result = await handler.RunAsync(new PredictTodaysRaceCardsOptions { DataDirectory = MockDataDirectory });

        result.Should().Be(ExitCodes.Success);
        var generatedPredictions = JsonSerializer.Deserialize<List<RaceCardPrediction>>(savedPredictionsAsJson!);

        generatedPredictions.Should().BeEquivalentTo(_predictionThatHorse1WillWin);
    }
}