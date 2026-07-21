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
    public async Task CarryStakeThroughToScore()
    {
        var predictionWithStake = new List<RaceCardPrediction>
        {
            new RaceCardPrediction
            {
                RaceId = 1,
                CourseId = 1,
                CourseName = "Course1",
                HorseId = 1,
                HorseName = "Horse1",
                Off = new DateTime(2022, 05, 13, 13, 40, 0),
                Stake = 2.5
            }
        };
        _mockFileSystem.File.ReadAllTextAsync(PredictionsFile)
            .Returns(Task.FromResult(await predictionWithStake.ToCsvString()));
        _mockFileSystem.Directory.Exists(MockDataDirectory).Returns(true);
        string? savedCsv = null;
        _mockFileSystem.File.WriteAllTextAsync(PredictionsScoresFile, Arg.Do<string>(x => savedCsv = x))
            .Returns(Task.CompletedTask);

        var handler = new ValidateRaceCardPredictionsCommandHandler(_mockFileSystem, new OutputLogger<ValidateRaceCardPredictionsCommandHandler>(_output));
        await handler.RunAsync(new ValidateRaceCardPredictionsOptions { DataDirectory = MockDataDirectory });

        var scores = await savedCsv!.FromCsvString<RaceCardPredictionScore>();
        scores.Single().Stake.Should().Be(2.5);
    }

    [Fact]
    public void ComputeAStakeWeightedReturnFromPerPickStakesAndOdds()
    {
        var scores = new List<RaceCardPredictionScore>
        {
            new() { Stake = 2.0, Won = true, DecimalOdds = 5.0, ResultStatus = ResultStatus.CompletedRace },
            new() { Stake = 3.0, Won = false, ResultStatus = ResultStatus.CompletedRace }
        };

        // (2·5 winnings − 3 loser stake) / 5 total staked = 1.40 -> 140%
        ValidateRaceCardPredictionsCommandHandler.StakeWeightedReturnPercentage(scores)
            .Should().Be(140.0);
    }

    [Fact]
    public void ReturnTheStakeForVoidOrNonRunnerPicksInTheStakeWeightedReturn()
    {
        var scores = new List<RaceCardPredictionScore>
        {
            new() { Stake = 2.0, Won = true, DecimalOdds = 6.0, ResultStatus = ResultStatus.CompletedRace },
            new() { Stake = 4.0, Won = false, ResultStatus = ResultStatus.CompletedRace },
            new() { Stake = 4.0, Won = false, ResultStatus = ResultStatus.RaceVoid }
        };

        // (2·6 winnings + 4 returned void stake − 4 loser stake) / 10 total staked = 1.20 -> 120%
        ValidateRaceCardPredictionsCommandHandler.StakeWeightedReturnPercentage(scores)
            .Should().Be(120.0);
    }

    [Fact]
    public void FallBackToTheFlatOnePoundReturnWhenNoStakesArePresent()
    {
        var scores = new List<RaceCardPredictionScore>
        {
            new() { Stake = null, Won = true, DecimalOdds = 11.0, ResultStatus = ResultStatus.CompletedRace },
            new() { Stake = null, Won = false, ResultStatus = ResultStatus.CompletedRace }
        };

        // No advised stakes -> treat each pick as a flat £1 bet: (11 winnings − 1 loser) / 2 = 500%.
        // The point is graceful degradation: a real number, never a divide-by-zero NaN.
        var result = ValidateRaceCardPredictionsCommandHandler.StakeWeightedReturnPercentage(scores);
        result.Should().Be(500.0);
        double.IsNaN(result).Should().BeFalse();
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
        scores.Single().Stake.Should().BeNull();
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
    public async Task SkipAPredictionWhoseRaceHasNoResultsAtAllAndStillScoreTheRest()
    {
        var predictionForAMissingRaceAndAKnownRace = new List<RaceCardPrediction>
        {
            new()
            {
                RaceId = 999,
                CourseId = 2,
                CourseName = "Course2",
                HorseId = 1,
                HorseName = "MissingRaceHorse",
                Off = new DateTime(2022, 05, 13, 21, 0, 0),
            },
            _predictionThatHorse1WillWin.Single()
        };
        _mockFileSystem.File.ReadAllTextAsync(PredictionsFile)
            .Returns(Task.FromResult(await predictionForAMissingRaceAndAKnownRace.ToCsvString()));
        _mockFileSystem.Directory.Exists(MockDataDirectory).Returns(true);
        string? savedCsv = null;
        _mockFileSystem.File.WriteAllTextAsync(PredictionsScoresFile, Arg.Do<string>(x => savedCsv = x))
            .Returns(Task.CompletedTask);

        var handler = new ValidateRaceCardPredictionsCommandHandler(_mockFileSystem, new OutputLogger<ValidateRaceCardPredictionsCommandHandler>(_output));
        var exitCode = await handler.RunAsync(new ValidateRaceCardPredictionsOptions { DataDirectory = MockDataDirectory });

        exitCode.Should().Be(ExitCodes.Success);
        var scores = await savedCsv!.FromCsvString<RaceCardPredictionScore>();
        scores.Should().BeEquivalentTo(_expectedPredictionScoreThatHorse1Won);
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

    [Fact]
    public async Task MergeAllPreRaceCardColumnsIntoMatchedResultRows()
    {
        // One card runner carrying every pre-race field; the result row is blank for all of them.
        var cards = new List<RaceCardRecord>
        {
            CardRunner(raceId: 1, horseId: 1, fractionalOdds: "11/2", decimalOdds: 6.5,
                officialRating: 95, racingPostRating: 102, topSpeedRating: 88,
                daysSinceLastRun: 21, formFigures: "1-234", prizeMoney: "£4,397", prizeMoneyValue: 4397m)
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
        horse1.CardOfficialRating.Should().Be(95);
        horse1.CardRacingPostRating.Should().Be(102);
        horse1.CardTopSpeedRating.Should().Be(88);
        horse1.DaysSinceLastRun.Should().Be(21);
        horse1.FormFigures.Should().Be("1-234");
        horse1.PrizeMoney.Should().Be("£4,397");
        horse1.PrizeMoneyValue.Should().Be(4397m);
    }

    [Fact]
    public async Task LeaveAlreadyPopulatedCardDataCellsUntouchedButFillStillBlankOnes()
    {
        // The result already has some pre-race cells filled (a prior run) and some still blank.
        var resultsWithSomeCardData = new List<RaceResultRecord>
        {
            new()
            {
                RaceId = 1, RaceName = "Race1", CourseId = 1, CourseName = "Course1", HorseId = 1,
                Off = new DateTime(2022, 05, 13, 13, 40, 0), FinishingPosition = 1,
                FractionalOdds = "10/1", DecimalOdds = 11, ResultStatus = ResultStatus.CompletedRace,
                CardOfficialRating = 50, DaysSinceLastRun = 7, FormFigures = "9-9",
                PrizeMoney = "£1", PrizeMoneyValue = 1m
                // CardRacingPostRating and CardTopSpeedRating left blank
            }
        };
        var cards = new List<RaceCardRecord>
        {
            CardRunner(raceId: 1, horseId: 1, fractionalOdds: "11/2", decimalOdds: 6.5,
                officialRating: 95, racingPostRating: 102, topSpeedRating: 88,
                daysSinceLastRun: 21, formFigures: "1-234", prizeMoney: "£4,397", prizeMoneyValue: 4397m)
        };
        var store = ConfigureStatefulFiles(
            (PredictionsFile, await _predictionThatHorse1WillWin.ToCsvString()),
            (RaceCardsFile, await cards.ToCsvString()),
            (ResultsFileForMay2022, await resultsWithSomeCardData.ToCsvString()));

        var handler = new ValidateRaceCardPredictionsCommandHandler(_mockFileSystem, new OutputLogger<ValidateRaceCardPredictionsCommandHandler>(_output));
        var exitCode = await handler.RunAsync(new ValidateRaceCardPredictionsOptions { DataDirectory = MockDataDirectory });

        exitCode.Should().Be(ExitCodes.Success);
        var mergedResults = await store[ResultsFileForMay2022].FromCsvString<RaceResultRecord>();
        var horse1 = mergedResults.Single(r => r.HorseId == 1);
        // Per-field idempotency: already-populated cells keep their own values, not the card's.
        horse1.CardOfficialRating.Should().Be(50);
        horse1.DaysSinceLastRun.Should().Be(7);
        horse1.FormFigures.Should().Be("9-9");
        horse1.PrizeMoney.Should().Be("£1");
        horse1.PrizeMoneyValue.Should().Be(1m);
        // Per-field blank-fill: still-blank cells DO fill from the card.
        horse1.CardRacingPostRating.Should().Be(102);
        horse1.CardTopSpeedRating.Should().Be(88);
    }

    [Fact]
    public async Task SourceCardRatingsFromTheCardNotThePostRaceResultRatings()
    {
        // The result already carries POST-RACE OR/RPR/TSR; the card carries the (different) PRE-RACE ones.
        var resultsWithPostRaceRatings = new List<RaceResultRecord>
        {
            new()
            {
                RaceId = 1, RaceName = "Race1", CourseId = 1, CourseName = "Course1", HorseId = 1,
                Off = new DateTime(2022, 05, 13, 13, 40, 0), FinishingPosition = 1,
                FractionalOdds = "10/1", DecimalOdds = 11, ResultStatus = ResultStatus.CompletedRace,
                OfficialRating = 130, RacingPostRating = 140, TopSpeedRating = 120
            }
        };
        var cards = new List<RaceCardRecord>
        {
            // No forecast price (SP), but the card does carry pre-race ratings — a rated race without a forecast.
            CardRunner(raceId: 1, horseId: 1, fractionalOdds: "SP", decimalOdds: null,
                officialRating: 95, racingPostRating: 102, topSpeedRating: 88)
        };
        var store = ConfigureStatefulFiles(
            (PredictionsFile, await _predictionThatHorse1WillWin.ToCsvString()),
            (RaceCardsFile, await cards.ToCsvString()),
            (ResultsFileForMay2022, await resultsWithPostRaceRatings.ToCsvString()));

        var handler = new ValidateRaceCardPredictionsCommandHandler(_mockFileSystem, new OutputLogger<ValidateRaceCardPredictionsCommandHandler>(_output));
        var exitCode = await handler.RunAsync(new ValidateRaceCardPredictionsOptions { DataDirectory = MockDataDirectory });

        exitCode.Should().Be(ExitCodes.Success);
        var mergedResults = await store[ResultsFileForMay2022].FromCsvString<RaceResultRecord>();
        var horse1 = mergedResults.Single(r => r.HorseId == 1);
        // Card* columns are sourced from the card's PRE-RACE figures...
        horse1.CardOfficialRating.Should().Be(95);
        horse1.CardRacingPostRating.Should().Be(102);
        horse1.CardTopSpeedRating.Should().Be(88);
        // ...while the inherited POST-RACE ratings on the result are left untouched (no leakage).
        horse1.OfficialRating.Should().Be(130);
        horse1.RacingPostRating.Should().Be(140);
        horse1.TopSpeedRating.Should().Be(120);
    }

    [Fact]
    public async Task ForwardOwnerFromTheCardIntoMatchedResultRows()
    {
        var cards = new List<RaceCardRecord>
        {
            CardRunner(raceId: 1, horseId: 1, fractionalOdds: "11/2", decimalOdds: 6.5,
                ownerId: 322703, ownerName: "Li Xiting")
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
        horse1.OwnerId.Should().Be(322703);
        horse1.OwnerName.Should().Be("Li Xiting");
    }

    [Fact]
    public async Task ForwardEveryOwnerBreedingAndExtraFieldFromTheCardIntoMatchedResultRows()
    {
        var cards = new List<RaceCardRecord>
        {
            CardRunner(raceId: 1, horseId: 1, fractionalOdds: "11/2", decimalOdds: 6.5,
                ownerId: 322703, ownerName: "Li Xiting",
                sireName: "Not A Single Doubt", sireCountry: "AUS", damName: "Jacquetta",
                headgearFirstTime: true, geldingFirstTime: false, windSurgery: 2,
                trainerRtf: 59, jockeyAllowanceLbs: 5, jockeyFirstTime: true,
                newTrainerRacesCount: 1, countryOfOrigin: "FR",
                spotlight: "Won well; \"one to note\", strong at C&D")
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
        horse1.OwnerId.Should().Be(322703);
        horse1.OwnerName.Should().Be("Li Xiting");
        horse1.SireName.Should().Be("Not A Single Doubt");
        horse1.SireCountry.Should().Be("AUS");
        horse1.DamName.Should().Be("Jacquetta");
        horse1.HeadgearFirstTime.Should().BeTrue();
        horse1.GeldingFirstTime.Should().BeFalse();
        horse1.WindSurgery.Should().Be(2);
        horse1.TrainerRtf.Should().Be(59);
        horse1.JockeyAllowanceLbs.Should().Be(5);
        horse1.JockeyFirstTime.Should().BeTrue();
        horse1.NewTrainerRacesCount.Should().Be(1);
        horse1.CountryOfOrigin.Should().Be("FR");
        horse1.Spotlight.Should().Be("Won well; \"one to note\", strong at C&D");
    }

    [Fact]
    public async Task LeaveResultOwnerBreedingExtrasCellsUntouchedWhenTheCardLacksThem()
    {
        var resultsWithOwnerData = new List<RaceResultRecord>
        {
            new()
            {
                RaceId = 1, RaceName = "Race1", CourseId = 1, CourseName = "Course1", HorseId = 1,
                Off = new DateTime(2022, 05, 13, 13, 40, 0), FinishingPosition = 1,
                FractionalOdds = "10/1", DecimalOdds = 11, ResultStatus = ResultStatus.CompletedRace,
                OwnerName = "Existing Owner", SireName = "Existing Sire", GeldingFirstTime = true
            }
        };
        // A matched card runner that genuinely carries none of the owner/breeding/extras fields.
        var cards = new List<RaceCardRecord> { CardRunner(raceId: 1, horseId: 1, fractionalOdds: "11/2", decimalOdds: 6.5) };
        var store = ConfigureStatefulFiles(
            (PredictionsFile, await _predictionThatHorse1WillWin.ToCsvString()),
            (RaceCardsFile, await cards.ToCsvString()),
            (ResultsFileForMay2022, await resultsWithOwnerData.ToCsvString()));

        var handler = new ValidateRaceCardPredictionsCommandHandler(_mockFileSystem, new OutputLogger<ValidateRaceCardPredictionsCommandHandler>(_output));
        var exitCode = await handler.RunAsync(new ValidateRaceCardPredictionsOptions { DataDirectory = MockDataDirectory });

        exitCode.Should().Be(ExitCodes.Success);
        var mergedResults = await store[ResultsFileForMay2022].FromCsvString<RaceResultRecord>();
        var horse1 = mergedResults.Single(r => r.HorseId == 1);
        // An absent card value never overwrites an existing result cell with empty data.
        horse1.OwnerName.Should().Be("Existing Owner");
        horse1.SireName.Should().Be("Existing Sire");
        horse1.GeldingFirstTime.Should().BeTrue();
        // And a still-blank result cell stays blank when the card has nothing to give.
        horse1.OwnerId.Should().BeNull();
        horse1.DamName.Should().BeNullOrEmpty();
    }

    [Fact]
    public async Task LeaveAlreadyPopulatedOwnerBreedingExtrasCellsUntouchedButFillStillBlankOnes()
    {
        var resultsWithSomeCardData = new List<RaceResultRecord>
        {
            new()
            {
                RaceId = 1, RaceName = "Race1", CourseId = 1, CourseName = "Course1", HorseId = 1,
                Off = new DateTime(2022, 05, 13, 13, 40, 0), FinishingPosition = 1,
                FractionalOdds = "10/1", DecimalOdds = 11, ResultStatus = ResultStatus.CompletedRace,
                OwnerName = "Existing Owner", SireName = "Existing Sire", WindSurgery = 1
                // OwnerId, DamName and TrainerRtf left blank
            }
        };
        var cards = new List<RaceCardRecord>
        {
            CardRunner(raceId: 1, horseId: 1, fractionalOdds: "11/2", decimalOdds: 6.5,
                ownerId: 322703, ownerName: "Li Xiting", sireName: "Not A Single Doubt",
                damName: "Jacquetta", windSurgery: 2, trainerRtf: 59)
        };
        var store = ConfigureStatefulFiles(
            (PredictionsFile, await _predictionThatHorse1WillWin.ToCsvString()),
            (RaceCardsFile, await cards.ToCsvString()),
            (ResultsFileForMay2022, await resultsWithSomeCardData.ToCsvString()));

        var handler = new ValidateRaceCardPredictionsCommandHandler(_mockFileSystem, new OutputLogger<ValidateRaceCardPredictionsCommandHandler>(_output));
        var exitCode = await handler.RunAsync(new ValidateRaceCardPredictionsOptions { DataDirectory = MockDataDirectory });

        exitCode.Should().Be(ExitCodes.Success);
        var mergedResults = await store[ResultsFileForMay2022].FromCsvString<RaceResultRecord>();
        var horse1 = mergedResults.Single(r => r.HorseId == 1);
        // Already-populated cells keep their own values, not the card's.
        horse1.OwnerName.Should().Be("Existing Owner");
        horse1.SireName.Should().Be("Existing Sire");
        horse1.WindSurgery.Should().Be(1);
        // Still-blank cells DO fill from the card.
        horse1.OwnerId.Should().Be(322703);
        horse1.DamName.Should().Be("Jacquetta");
        horse1.TrainerRtf.Should().Be(59);
    }

    [Fact]
    public async Task CarryAFirstTimeFlagCapturedAsFalseOntoTheResultAsFalseNotNull()
    {
        var cards = new List<RaceCardRecord>
        {
            CardRunner(raceId: 1, horseId: 1, fractionalOdds: "11/2", decimalOdds: 6.5,
                headgearFirstTime: true, geldingFirstTime: false)
            // jockeyFirstTime left null on the card
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
        // Gated on presence, not truthiness: a captured false survives as false, distinct from an absent (null) flag.
        horse1.HeadgearFirstTime.Should().BeTrue();
        horse1.GeldingFirstTime.Should().BeFalse();
        horse1.JockeyFirstTime.Should().BeNull();
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

    private static RaceCardRecord CardRunner(int raceId, int horseId, string fractionalOdds, double? decimalOdds,
        int? officialRating = null, int? racingPostRating = null, int? topSpeedRating = null,
        int? daysSinceLastRun = null, string? formFigures = null, string? prizeMoney = null, decimal? prizeMoneyValue = null,
        int? ownerId = null, string? ownerName = null, string? sireName = null, string? sireCountry = null,
        string? damName = null, bool? headgearFirstTime = null, bool? geldingFirstTime = null, int? windSurgery = null,
        int? trainerRtf = null, int? jockeyAllowanceLbs = null, bool? jockeyFirstTime = null,
        int? newTrainerRacesCount = null, string? countryOfOrigin = null, string? spotlight = null) =>
        new()
        {
            RaceId = raceId,
            RaceName = "Race1",
            CourseId = 1,
            CourseName = "Course1",
            HorseId = horseId,
            Off = new DateTime(2022, 05, 13, 13, 40, 0),
            FractionalOdds = fractionalOdds,
            DecimalOdds = decimalOdds,
            OfficialRating = officialRating,
            RacingPostRating = racingPostRating,
            TopSpeedRating = topSpeedRating,
            DaysSinceLastRun = daysSinceLastRun,
            FormFigures = formFigures,
            PrizeMoney = prizeMoney,
            PrizeMoneyValue = prizeMoneyValue,
            OwnerId = ownerId,
            OwnerName = ownerName,
            SireName = sireName,
            SireCountry = sireCountry,
            DamName = damName,
            HeadgearFirstTime = headgearFirstTime,
            GeldingFirstTime = geldingFirstTime,
            WindSurgery = windSurgery,
            TrainerRtf = trainerRtf,
            JockeyAllowanceLbs = jockeyAllowanceLbs,
            JockeyFirstTime = jockeyFirstTime,
            NewTrainerRacesCount = newTrainerRacesCount,
            CountryOfOrigin = countryOfOrigin,
            Spotlight = spotlight
        };

    // Backs the mock filesystem with a mutable store so Exists/Read/Delete/Write behave like a real one.
    // Lets the merge rewrite the results file without brittle call-count sequencing on the mock.
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
