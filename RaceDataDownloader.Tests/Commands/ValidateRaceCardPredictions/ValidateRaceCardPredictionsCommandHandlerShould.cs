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
    private const string RaceCardsFile = @"c:\out\TodaysRaceCards.csv";

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
    public async Task CarryWinProbabilityThroughToScore()
    {
        var predictionWithWinProbability = new List<RaceCardPrediction>
        {
            new RaceCardPrediction
            {
                RaceId = 1,
                CourseId = 1,
                CourseName = "Course1",
                HorseId = 1,
                HorseName = "Horse1",
                Off = new DateTime(2022, 05, 13, 13, 40, 0),
                WinProbability = 0.4
            }
        };
        _mockFileSystem.File.ReadAllTextAsync(PredictionsFile)
            .Returns(Task.FromResult(await predictionWithWinProbability.ToCsvString()));
        _mockFileSystem.Directory.Exists(MockDataDirectory).Returns(true);
        string? savedCsv = null;
        _mockFileSystem.File.WriteAllTextAsync(PredictionsScoresFile, Arg.Do<string>(x => savedCsv = x))
            .Returns(Task.CompletedTask);

        var handler = new ValidateRaceCardPredictionsCommandHandler(_mockFileSystem, new OutputLogger<ValidateRaceCardPredictionsCommandHandler>(_output));
        await handler.RunAsync(new ValidateRaceCardPredictionsOptions { DataDirectory = MockDataDirectory });

        var scores = await savedCsv!.FromCsvString<RaceCardPredictionScore>();
        scores.Single().WinProbability.Should().Be(0.4);
    }

    [Fact]
    public async Task HandleLegacyPredictionsFileMissingWinProbabilityWithoutThrowing()
    {
        // Simulate a legacy TodaysPredictions.csv that has no WinProbability column
        var legacyPrediction = new { RaceId = 1, CourseId = 1, CourseName = "Course1", Off = new DateTime(2022, 05, 13, 13, 40, 0), HorseId = 1, HorseName = "Horse1" };
        var legacyCsv = await new[] { legacyPrediction }.ToCsvString();
        _mockFileSystem.File.ReadAllTextAsync(PredictionsFile).Returns(Task.FromResult(legacyCsv));
        _mockFileSystem.Directory.Exists(MockDataDirectory).Returns(true);
        string? savedCsv = null;
        _mockFileSystem.File.WriteAllTextAsync(PredictionsScoresFile, Arg.Do<string>(x => savedCsv = x))
            .Returns(Task.CompletedTask);

        var handler = new ValidateRaceCardPredictionsCommandHandler(_mockFileSystem, new OutputLogger<ValidateRaceCardPredictionsCommandHandler>(_output));
        var exitCode = await handler.RunAsync(new ValidateRaceCardPredictionsOptions { DataDirectory = MockDataDirectory });

        exitCode.Should().Be(ExitCodes.Success);
        var scores = await savedCsv!.FromCsvString<RaceCardPredictionScore>();
        scores.Single().WinProbability.Should().BeNull();
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

    [Fact]
    public async Task MergeForecastOddsFromTheCardIntoMatchedResultRows()
    {
        var cards = new List<RaceCardRecord>
        {
            CardRunner(raceId: 1, horseId: 1, fractionalOdds: "11/2", decimalOdds: 6.5),
            CardRunner(raceId: 1, horseId: 2, fractionalOdds: "SP", decimalOdds: null)
        };
        var store = ConfigureStatefulFiles(
            (PredictionsFile, await _predictionThatHorse1WillWin.ToCsvString()),
            (RaceCardsFile, await cards.ToCsvString()),
            (ResultsFileForMay2022, await _resultsWhereHorse1Won.ToCsvString()));

        var handler = new ValidateRaceCardPredictionsCommandHandler(_mockFileSystem, new OutputLogger<ValidateRaceCardPredictionsCommandHandler>(_output));
        var exitCode = await handler.RunAsync(new ValidateRaceCardPredictionsOptions { DataDirectory = MockDataDirectory });

        exitCode.Should().Be(ExitCodes.Success);
        var mergedResults = await store[ResultsFileForMay2022].FromCsvString<RaceResultRecord>();
        var horse1 = mergedResults.Single(r => r.HorseId == 1);
        horse1.ForecastFractionalOdds.Should().Be("11/2");
        horse1.ForecastDecimalOdds.Should().Be(6.5);
    }

    [Fact]
    public async Task LeaveAlreadyPopulatedForecastOddsUntouchedOnReRun()
    {
        var resultsWithExistingForecast = new List<RaceResultRecord>
        {
            new()
            {
                RaceId = 1, RaceName = "Race1", CourseId = 1, CourseName = "Course1", HorseId = 1,
                Off = new DateTime(2022, 05, 13, 13, 40, 0), FinishingPosition = 1,
                FractionalOdds = "10/1", DecimalOdds = 11, ResultStatus = ResultStatus.CompletedRace,
                ForecastFractionalOdds = "100/1", ForecastDecimalOdds = 101
            }
        };
        var cards = new List<RaceCardRecord> { CardRunner(raceId: 1, horseId: 1, fractionalOdds: "11/2", decimalOdds: 6.5) };
        var store = ConfigureStatefulFiles(
            (PredictionsFile, await _predictionThatHorse1WillWin.ToCsvString()),
            (RaceCardsFile, await cards.ToCsvString()),
            (ResultsFileForMay2022, await resultsWithExistingForecast.ToCsvString()));

        var handler = new ValidateRaceCardPredictionsCommandHandler(_mockFileSystem, new OutputLogger<ValidateRaceCardPredictionsCommandHandler>(_output));
        var exitCode = await handler.RunAsync(new ValidateRaceCardPredictionsOptions { DataDirectory = MockDataDirectory });

        exitCode.Should().Be(ExitCodes.Success);
        var mergedResults = await store[ResultsFileForMay2022].FromCsvString<RaceResultRecord>();
        var horse1 = mergedResults.Single(r => r.HorseId == 1);
        horse1.ForecastFractionalOdds.Should().Be("100/1");
        horse1.ForecastDecimalOdds.Should().Be(101);
    }

    [Fact]
    public async Task CompleteSuccessfullyAndLeaveResultsUnchangedWhenCardFileIsMissing()
    {
        // No TodaysRaceCards.csv in the store - the merge must skip gracefully.
        var store = ConfigureStatefulFiles(
            (PredictionsFile, await _predictionThatHorse1WillWin.ToCsvString()),
            (ResultsFileForMay2022, await _resultsWhereHorse1Won.ToCsvString()));

        var handler = new ValidateRaceCardPredictionsCommandHandler(_mockFileSystem, new OutputLogger<ValidateRaceCardPredictionsCommandHandler>(_output));
        var exitCode = await handler.RunAsync(new ValidateRaceCardPredictionsOptions { DataDirectory = MockDataDirectory });

        exitCode.Should().Be(ExitCodes.Success);
        var results = await store[ResultsFileForMay2022].FromCsvString<RaceResultRecord>();
        results.Should().OnlyContain(r => string.IsNullOrEmpty(r.ForecastFractionalOdds) && r.ForecastDecimalOdds == null);
    }

    [Fact]
    public async Task LeaveResultRowsWithoutARealCardForecastUnfilled()
    {
        var results = new List<RaceResultRecord>
        {
            ResultRunner(horseId: 1, fractionalOdds: "10/1", decimalOdds: 11, finishingPosition: 1),
            ResultRunner(horseId: 2, fractionalOdds: "5/2", decimalOdds: 3.5, finishingPosition: 2),
            ResultRunner(horseId: 3, fractionalOdds: "7/1", decimalOdds: 8, finishingPosition: 3)
        };
        var cards = new List<RaceCardRecord>
        {
            CardRunner(raceId: 1, horseId: 1, fractionalOdds: "11/2", decimalOdds: 6.5), // real forecast
            CardRunner(raceId: 1, horseId: 2, fractionalOdds: "SP", decimalOdds: null)   // no real forecast
            // horse 3 is absent from the card entirely
        };
        var store = ConfigureStatefulFiles(
            (PredictionsFile, await _predictionThatHorse1WillWin.ToCsvString()),
            (RaceCardsFile, await cards.ToCsvString()),
            (ResultsFileForMay2022, await results.ToCsvString()));

        var handler = new ValidateRaceCardPredictionsCommandHandler(_mockFileSystem, new OutputLogger<ValidateRaceCardPredictionsCommandHandler>(_output));
        var exitCode = await handler.RunAsync(new ValidateRaceCardPredictionsOptions { DataDirectory = MockDataDirectory });

        exitCode.Should().Be(ExitCodes.Success);
        var mergedResults = await store[ResultsFileForMay2022].FromCsvString<RaceResultRecord>();
        mergedResults.Single(r => r.HorseId == 1).ForecastDecimalOdds.Should().Be(6.5);
        mergedResults.Single(r => r.HorseId == 2).ForecastDecimalOdds.Should().BeNull();
        mergedResults.Single(r => r.HorseId == 2).ForecastFractionalOdds.Should().BeNullOrEmpty();
        mergedResults.Single(r => r.HorseId == 3).ForecastDecimalOdds.Should().BeNull();
        mergedResults.Single(r => r.HorseId == 3).ForecastFractionalOdds.Should().BeNullOrEmpty();
    }

    private static RaceResultRecord ResultRunner(int horseId, string fractionalOdds, double decimalOdds, int finishingPosition) =>
        new()
        {
            RaceId = 1,
            RaceName = "Race1",
            CourseId = 1,
            CourseName = "Course1",
            HorseId = horseId,
            Off = new DateTime(2022, 05, 13, 13, 40, 0),
            FinishingPosition = finishingPosition,
            FractionalOdds = fractionalOdds,
            DecimalOdds = decimalOdds,
            ResultStatus = ResultStatus.CompletedRace
        };

    private static RaceCardRecord CardRunner(int raceId, int horseId, string fractionalOdds, double? decimalOdds) =>
        new()
        {
            RaceId = raceId,
            RaceName = "Race1",
            CourseId = 1,
            CourseName = "Course1",
            HorseId = horseId,
            Off = new DateTime(2022, 05, 13, 13, 40, 0),
            FractionalOdds = fractionalOdds,
            DecimalOdds = decimalOdds
        };

    /// <summary>
    /// Wires the mock filesystem to behave like a real one for the supplied files: Exists/ReadAllText
    /// are backed by a mutable store, Delete removes from it and WriteAllText writes back to it. This lets
    /// the merge rewrite the results file (DeleteFileIfExists then WriteAllText) without brittle call-count
    /// sequencing. Returns the store so a test can read back what was written.
    /// </summary>
    private Dictionary<string, string> ConfigureStatefulFiles(params (string name, string content)[] files)
    {
        var store = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        foreach (var (name, content) in files)
        {
            store[name] = content;
        }

        _mockFileSystem.Directory.Exists(MockDataDirectory).Returns(true);
        _mockFileSystem.File.Exists(Arg.Any<string>()).Returns(ci => store.ContainsKey(ci.Arg<string>()));
        _mockFileSystem.File.ReadAllTextAsync(Arg.Any<string>()).Returns(ci => Task.FromResult(store[ci.Arg<string>()]));
        _mockFileSystem.File.When(x => x.Delete(Arg.Any<string>())).Do(ci => store.Remove(ci.Arg<string>()));
        _mockFileSystem.File
            .When(x => x.WriteAllTextAsync(Arg.Any<string>(), Arg.Any<string?>()))
            .Do(ci => store[ci.ArgAt<string>(0)] = ci.ArgAt<string>(1) ?? string.Empty);
        return store;
    }
}
