using System.ComponentModel.DataAnnotations;
using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using RaceDataDownloader.Models;
using RacePredictor.Core;

namespace RaceDataDownloader.Commands.ValidateRaceCardPredictions;

public class ValidateRaceCardPredictionsCommandHandler(
    IFileSystem fileSystem,
    ILogger<ValidateRaceCardPredictionsCommandHandler> logger)
    :
        FileCommandHandlerBase<ValidateRaceCardPredictionsCommandHandler, ValidateRaceCardPredictionsOptions>(
            fileSystem, logger)
{
    private readonly Dictionary<string, List<RaceResultRecord>> _resultsCache = new();
    private string _dataFolder = string.Empty;


    protected override async Task InternalRunAsync(ValidateRaceCardPredictionsOptions options)
    {
        _dataFolder = ValidateAndCreateOutputFolder(options.DataDirectory);

        await MergeForecastOddsIntoResults();

        var predictions = await FileSystem.ReadRecordsFromCsvFile<RaceCardPrediction>(Path.Combine(_dataFolder, "TodaysPredictions.csv"));
        Logger.LogInformation("Scoring {PredictionCount} predictions for today", predictions.Count);

        var scores = await ScorePredictions(predictions).ToListAsync();
        if (scores.Count > 0)
        {
            await MergePredictionScores(scores);

            // Calculate winnings and losses based on a £1 bet on each race
            var stake = scores.Count;
            var losses = scores.Count(x => !x.Won && !StakeReturnedFor(x.ResultStatus));
            var returned = scores.Count(x => StakeReturnedFor(x.ResultStatus));
            var winnings = scores.Where(x => x.Won).Sum(x => x.DecimalOdds ?? 0) + returned;
            var percentageGains = (winnings - losses) / stake * 100.0;
            Logger.LogInformation("Scored {ScoredCount} predictions so far this month.", scores.Count);
            Logger.LogInformation(
                "With a £{Stake} stake and {Losses} losses, total winnings would be £{Winnings:00} representing a {PercentageGains:00}% gain/loss.",
                stake,
                losses,
                winnings,
                percentageGains);
        }
    }

    // Runs before TodaysRaceCards.csv is overwritten: copies the morning forecast onto matching
    // (RaceId, HorseId) result rows. Idempotent — only blank cells are filled.
    private async Task MergeForecastOddsIntoResults()
    {
        var cardFileName = Path.Combine(_dataFolder, "TodaysRaceCards.csv");
        if (!FileSystem.File.Exists(cardFileName))
        {
            Logger.LogInformation("No race card file at {CardFile}; skipping forecast-odds merge.", cardFileName);
            return;
        }

        var cards = await FileSystem.ReadRecordsFromCsvFile<RaceCardRecord>(cardFileName);

        // A non-null decimal marks a real forecast; runners left at the "SP" default must not overwrite results.
        var forecastByRunner = cards
            .Where(c => c.DecimalOdds != null)
            .GroupBy(c => (c.RaceId, c.HorseId))
            .ToDictionary(g => g.Key, g => g.Last());

        if (forecastByRunner.Count == 0)
        {
            Logger.LogInformation("No forecast odds present on {CardFile}; nothing to merge into results.", cardFileName);
            return;
        }

        var resultsFileNames = cards
            .Select(c => FileSystem.GetResultsFileName(_dataFolder, DateOnly.FromDateTime(c.Off)))
            .Distinct();

        foreach (var resultsFileName in resultsFileNames)
        {
            if (!FileSystem.File.Exists(resultsFileName))
            {
                Logger.LogInformation("No results file at {ResultsFile}; skipping forecast-odds merge for it.", resultsFileName);
                continue;
            }

            var results = await FileSystem.ReadRecordsFromCsvFile<RaceResultRecord>(resultsFileName);
            var filled = 0;
            foreach (var result in results)
            {
                if (result.ForecastDecimalOdds != null || !string.IsNullOrEmpty(result.ForecastFractionalOdds))
                {
                    continue;
                }

                if (forecastByRunner.TryGetValue((result.RaceId, result.HorseId), out var forecast))
                {
                    result.ForecastFractionalOdds = forecast.FractionalOdds;
                    result.ForecastDecimalOdds = forecast.DecimalOdds;
                    filled++;
                }
            }

            if (filled > 0)
            {
                await FileSystem.WriteRecordsToCsvFile(resultsFileName, results);
            }

            Logger.LogInformation("Merged forecast odds into {Filled} of {Total} result rows in {ResultsFile}.", filled, results.Count, resultsFileName);
        }
    }

    private static bool StakeReturnedFor(ResultStatus resultStatus) =>
        resultStatus is ResultStatus.RaceVoid or ResultStatus.NonRunner;

    private async Task MergePredictionScores(List<RaceCardPredictionScore> scores)
    {
        var start = DateOnly.FromDateTime(scores.Min(x => x.Off));
        var predictionsFileName = FileSystem.GetPredictionScoresFileName(_dataFolder, start);
        if (FileSystem.File.Exists(predictionsFileName))
        {
            var existingScores = await FileSystem.ReadRecordsFromCsvFile<RaceCardPredictionScore>(predictionsFileName);
            foreach (var existingScore in existingScores)
            {
                if (!scores.Any(x => x.RaceId == existingScore.RaceId && x.HorseId == existingScore.HorseId))
                {
                    scores.Add(existingScore);
                }
            }
        }

        await FileSystem.WriteRecordsToCsvFile(predictionsFileName, scores);
    }

    private async IAsyncEnumerable<RaceCardPredictionScore> ScorePredictions(List<RaceCardPrediction> predictions)
    {
        foreach (var prediction in predictions)
        {
            var result = await FindResultForPrediction(prediction);
            yield return new RaceCardPredictionScore
            {
                RaceId = prediction.RaceId,
                CourseId = prediction.CourseId,
                CourseName = prediction.CourseName,
                Off = prediction.Off,
                HorseId = prediction.HorseId,
                HorseName = prediction.HorseName,
                WinProbability = prediction.WinProbability,
                Stake = prediction.Stake,
                FinishingPosition = result.FinishingPosition,
                Won = result.FinishingPosition == 1,
                FractionalOdds = result.FractionalOdds,
                DecimalOdds = result.DecimalOdds,
                ResultStatus = result.ResultStatus
            };
        }
    }

    private async Task<RaceResultRecord> FindResultForPrediction(RaceCardPrediction prediction)
    {
        var predictionRaceDate = DateOnly.FromDateTime(prediction.Off);
        var resultsForDate = await EnsureResultsLoadedFor(prediction.RaceId, predictionRaceDate);
        if (resultsForDate.Count == 0)
        {
            throw new ValidationException($"Unable to find race results for race {prediction.RaceId} on {prediction.Off}");
        }

        var resultForPrediction =
            resultsForDate.FirstOrDefault(r => r.HorseId == prediction.HorseId);
        if (resultForPrediction == null)
        {
            Logger.LogWarning("Unable to find horse {HorseName} ({HorseId}) in race results for race {RaceId} on {Off} - assuming non-runner",
                prediction.HorseId, prediction.HorseName, prediction.RaceId, prediction.Off);
            return new RaceResultRecord
            {
                HorseId = prediction.HorseId,
                HorseName = prediction.HorseName,
                RaceId = prediction.RaceId,
                CourseId = prediction.CourseId,
                CourseName = prediction.CourseName,
                Off = prediction.Off,
                ResultStatus = ResultStatus.NonRunner,
            };
        }

        return resultForPrediction;
    }

    private async Task<List<RaceResultRecord>> EnsureResultsLoadedFor(int raceId, DateOnly date)
    {
        var resultsFileName = FileSystem.GetResultsFileName(_dataFolder, date);
        if (!_resultsCache.TryGetValue(resultsFileName, out var resultsForMonth))
        {
            if (!FileSystem.File.Exists(resultsFileName))
            {
                return new List<RaceResultRecord>();
            }

            resultsForMonth = await FileSystem.ReadRecordsFromCsvFile<RaceResultRecord>(resultsFileName);
            _resultsCache.Add(resultsFileName, resultsForMonth);
        }

        var start = date.ToDateTime(TimeOnly.MinValue);
        var end = start.AddDays(1);
        return resultsForMonth.Where(r => r.RaceId == raceId && r.Off >= start && r.Off < end).ToList();
    }
}
