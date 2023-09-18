using System.ComponentModel.DataAnnotations;
using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using RaceDataDownloader.Models;
using RacePredictor.Core;

namespace RaceDataDownloader.Commands.ValidateRaceCardPredictions;

public class ValidateRaceCardPredictionsCommandHandler :
    FileCommandHandlerBase<ValidateRaceCardPredictionsCommandHandler, ValidateRaceCardPredictionsOptions>
{
    private readonly Dictionary<string, List<RaceResultRecord>> _resultsCache = new();
    private string _dataFolder = string.Empty;


    public ValidateRaceCardPredictionsCommandHandler(
        IFileSystem fileSystem,
        ILogger<ValidateRaceCardPredictionsCommandHandler> logger) : base(fileSystem, logger)
    {
    }

    protected override async Task InternalRunAsync(ValidateRaceCardPredictionsOptions options)
    {
        _dataFolder = ValidateAndCreateOutputFolder(options.DataDirectory);
        var predictions = await FileSystem.ReadRecordsFromCsvFile<RaceCardPrediction>(Path.Combine(_dataFolder, "TodaysPredictions.csv"));
        Logger.LogInformation("Scoring {PredictionCount} predictions for today", predictions.Count);

        var scores = await ScorePredictions(predictions).ToListAsync();
        if (scores.Any())
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
