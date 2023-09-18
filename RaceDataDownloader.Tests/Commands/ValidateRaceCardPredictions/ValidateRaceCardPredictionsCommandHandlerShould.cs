using System.IO.Abstractions;
using NSubstitute;
using RaceDataDownloader.Commands;
using RaceDataDownloader.Commands.ValidateRaceCardPredictions;
using RaceDataDownloader.Models;
using RacePredictor.Core;
using Xunit.Abstractions;

namespace RaceDataDownloader.Tests.Commands.ValidateRaceCardPredictions;

public class ValidateRaceCardPredictionsCommandHandlerShould
{
    private const string MockDataDirectory = @"c:\out";
    private const string ResultsFileForMay2022 = @"c:\out\Results_202205.csv";
    private const string PredictionsFile = @"c:\out\TodaysPredictions.csv";
    private const string PredictionsScoresFile = @"c:\out\PredictionScores_202205.csv";

    private readonly ITestOutputHelper _output;
    private readonly IFileSystem _mockFileSystem;
    private readonly List<RaceCardPrediction> _predictionThatHorse1WillWin = new()
    {
        new RaceCardPrediction
        {
            RaceId = 1,
            CourseId = 1,
            CourseName = "Course1",
            HorseId = 1,
            HorseName = "Horse1",
            Off = new DateTime(2022, 05, 13, 13, 40, 0),
        }
    };

    private readonly List<RaceResultRecord> _resultsWhereHorse1Won = new()
    {
        new RaceResultRecord
        {
            RaceId = 1,
            RaceName = "Race1",
            CourseId = 1,
            CourseName = "Course1",
            HorseId = 1,
            Off = new DateTime(2022, 05, 13, 13, 40, 0),
            FinishingPosition = 1,
            FractionalOdds = "10/1",
            DecimalOdds = 11,
            ResultStatus = ResultStatus.CompletedRace
        },
        new RaceResultRecord
        {
            RaceId = 1,
            RaceName = "Race1",
            CourseId = 1,
            CourseName = "Course1",
            HorseId = 2,
            Off = new DateTime(2022, 05, 13, 13, 40, 0),
            FinishingPosition = 2,
            FractionalOdds = "5/2",
            DecimalOdds = 3.5,
            ResultStatus = ResultStatus.CompletedRace
        }
    };

    private readonly List<RaceCardPredictionScore> _expectedPredictionScoreThatHorse1Won = new()
    {
        new RaceCardPredictionScore
        {
            RaceId = 1,
            CourseId = 1,
            CourseName = "Course1",
            HorseId = 1,
            HorseName = "Horse1",
            Off = new DateTime(2022, 05, 13, 13, 40, 0),
            FinishingPosition = 1,
            Won = true,
            FractionalOdds = "10/1",
            DecimalOdds = 11,
            ResultStatus = ResultStatus.CompletedRace
        }
    };

    public ValidateRaceCardPredictionsCommandHandlerShould(ITestOutputHelper output)
    {
        _output = output;
        _mockFileSystem = Substitute.For<IFileSystem>();
        _mockFileSystem.File.ReadAllTextAsync(ResultsFileForMay2022).Returns(Task.FromResult(_resultsWhereHorse1Won.ToCsvString().Result));
        _mockFileSystem.File.Exists(ResultsFileForMay2022).Returns(true);

        _mockFileSystem.File.ReadAllTextAsync(PredictionsFile).Returns(Task.FromResult(_predictionThatHorse1WillWin.ToCsvString().Result));
        _mockFileSystem.File.Exists(PredictionsFile).Returns(true);
    }

    [Fact]
    public async Task ScorePredictionThatHorse1WillWinAsWon()
    {
        _mockFileSystem.Directory.Exists(MockDataDirectory).Returns(true);
        string? savedPredictionsScoresAsCsv = null;
        _mockFileSystem.File.WriteAllTextAsync(PredictionsScoresFile, Arg.Do<string>(x => savedPredictionsScoresAsCsv = x))
            .Returns(Task.CompletedTask);

        var logger = new OutputLogger<ValidateRaceCardPredictionsCommandHandler>(_output);

        var handler = new ValidateRaceCardPredictionsCommandHandler(_mockFileSystem, logger);
        var result = await handler.RunAsync(new ValidateRaceCardPredictionsOptions { DataDirectory = MockDataDirectory });

        result.Should().Be(ExitCodes.Success);
        var generatedPredictionScores = await savedPredictionsScoresAsCsv!.FromCsvString<RaceCardPredictionScore>();

        generatedPredictionScores.Should().BeEquivalentTo(_expectedPredictionScoreThatHorse1Won);
    }
}
