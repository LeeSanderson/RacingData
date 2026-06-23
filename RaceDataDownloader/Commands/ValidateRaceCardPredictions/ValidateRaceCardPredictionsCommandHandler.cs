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

        await MergeCardDataIntoResults();

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

            // Staked performance using the advised per-pick Stake; falls back to the flat-£1 figure above
            // when no stakes are present (no-bet day).
            var advisedStake = scores.Sum(x => x.Stake ?? 0);
            var stakeWeightedGains = StakeWeightedReturnPercentage(scores);
            Logger.LogInformation(
                "Stake-weighted: across £{AdvisedStake:0.00} advised on staked picks, the return would be {StakeWeightedGains:00}% gain/loss.",
                advisedStake,
                stakeWeightedGains);
        }
    }

    // Runs before TodaysRaceCards.csv is overwritten: copies the morning racecard's pre-race data onto
    // matching (RaceId, HorseId) result rows. Forward-only and idempotent — each field is filled only
    // when the card has it AND the result cell is still blank.
    private async Task MergeCardDataIntoResults()
    {
        var cardFileName = Path.Combine(_dataFolder, "TodaysRaceCards.csv");
        if (!FileSystem.File.Exists(cardFileName))
        {
            Logger.LogInformation("No race card file at {CardFile}; skipping card-data merge.", cardFileName);
            return;
        }

        var cards = await FileSystem.ReadRecordsFromCsvFile<RaceCardRecord>(cardFileName);

        // Index ALL card runners (not just those carrying a forecast price): ratings/form/prize merge even
        // for a runner left at the "SP" forecast default. The forecast-odds copy itself still gates on a
        // real (non-null) decimal inside MergeCardRunnerIntoResult, so its behaviour is unchanged.
        var cardByRunner = cards
            .GroupBy(c => (c.RaceId, c.HorseId))
            .ToDictionary(g => g.Key, g => g.Last());

        if (cardByRunner.Count == 0)
        {
            Logger.LogInformation("No runners on {CardFile}; nothing to merge into results.", cardFileName);
            return;
        }

        var resultsFileNames = cards
            .Select(c => FileSystem.GetResultsFileName(_dataFolder, DateOnly.FromDateTime(c.Off)))
            .Distinct();

        foreach (var resultsFileName in resultsFileNames)
        {
            if (!FileSystem.File.Exists(resultsFileName))
            {
                Logger.LogInformation("No results file at {ResultsFile}; skipping card-data merge for it.", resultsFileName);
                continue;
            }

            var results = await FileSystem.ReadRecordsFromCsvFile<RaceResultRecord>(resultsFileName);
            var cellsFilled = 0;
            foreach (var result in results)
            {
                if (cardByRunner.TryGetValue((result.RaceId, result.HorseId), out var card))
                {
                    cellsFilled += MergeCardRunnerIntoResult(card, result);
                }
            }

            if (cellsFilled > 0)
            {
                await FileSystem.WriteRecordsToCsvFile(resultsFileName, results);
            }

            Logger.LogInformation("Merged card data: filled {Filled} blank cell(s) across {Total} result rows in {ResultsFile}.", cellsFilled, results.Count, resultsFileName);
        }
    }

    // Copies each pre-race field from the card runner onto the result row only when the card carries the
    // value AND the result cell is still blank (per-field presence + per-field blank-fill). Returns the
    // number of cells filled, so the caller rewrites a results file only when at least one cell changed.
    private static int MergeCardRunnerIntoResult(RaceCardRecord card, RaceResultRecord result)
    {
        var filled = 0;

        // Forecast odds — the original two-column rule, preserved exactly: a non-null decimal marks a real
        // forecast (runners left at the "SP" default must not overwrite results), and the fractional and
        // decimal columns are treated as a single unit gated on the two-column blank check.
        if (card.DecimalOdds != null &&
            result.ForecastDecimalOdds == null && string.IsNullOrEmpty(result.ForecastFractionalOdds))
        {
            result.ForecastFractionalOdds = card.FractionalOdds;
            result.ForecastDecimalOdds = card.DecimalOdds;
            filled++;
        }

        // Pre-race ratings: card OR/RPR/TSR → result Card* columns, kept distinct from the inherited
        // post-race OfficialRating/RacingPostRating/TopSpeedRating so the non-leaky figures are preserved.
        if (card.OfficialRating != null && result.CardOfficialRating == null)
        {
            result.CardOfficialRating = card.OfficialRating;
            filled++;
        }
        if (card.RacingPostRating != null && result.CardRacingPostRating == null)
        {
            result.CardRacingPostRating = card.RacingPostRating;
            filled++;
        }
        if (card.TopSpeedRating != null && result.CardTopSpeedRating == null)
        {
            result.CardTopSpeedRating = card.TopSpeedRating;
            filled++;
        }

        // Days-since/form/prize forward name-to-name: card and result each own these columns at their own
        // sibling indices, so the value carries straight across with no Card* prefix.
        if (card.DaysSinceLastRun != null && result.DaysSinceLastRun == null)
        {
            result.DaysSinceLastRun = card.DaysSinceLastRun;
            filled++;
        }
        if (!string.IsNullOrEmpty(card.FormFigures) && string.IsNullOrEmpty(result.FormFigures))
        {
            result.FormFigures = card.FormFigures;
            filled++;
        }
        if (!string.IsNullOrEmpty(card.PrizeMoney) && string.IsNullOrEmpty(result.PrizeMoney))
        {
            result.PrizeMoney = card.PrizeMoney;
            filled++;
        }
        if (card.PrizeMoneyValue != null && result.PrizeMoneyValue == null)
        {
            result.PrizeMoneyValue = card.PrizeMoneyValue;
            filled++;
        }

        if (card.OwnerId != null && result.OwnerId == null)
        {
            result.OwnerId = card.OwnerId;
            filled++;
        }
        if (!string.IsNullOrEmpty(card.OwnerName) && string.IsNullOrEmpty(result.OwnerName))
        {
            result.OwnerName = card.OwnerName;
            filled++;
        }

        // The three first-time flags gate on presence (non-null), never truthiness, so a card `false` is
        // carried as `false` and stays distinct from an absent (null) flag — the three-state signal is preserved.
        if (card.HeadgearFirstTime != null && result.HeadgearFirstTime == null)
        {
            result.HeadgearFirstTime = card.HeadgearFirstTime;
            filled++;
        }
        if (card.GeldingFirstTime != null && result.GeldingFirstTime == null)
        {
            result.GeldingFirstTime = card.GeldingFirstTime;
            filled++;
        }
        if (card.JockeyFirstTime != null && result.JockeyFirstTime == null)
        {
            result.JockeyFirstTime = card.JockeyFirstTime;
            filled++;
        }

        if (!string.IsNullOrEmpty(card.SireName) && string.IsNullOrEmpty(result.SireName))
        {
            result.SireName = card.SireName;
            filled++;
        }
        if (!string.IsNullOrEmpty(card.SireCountry) && string.IsNullOrEmpty(result.SireCountry))
        {
            result.SireCountry = card.SireCountry;
            filled++;
        }
        if (!string.IsNullOrEmpty(card.DamName) && string.IsNullOrEmpty(result.DamName))
        {
            result.DamName = card.DamName;
            filled++;
        }
        if (card.WindSurgery != null && result.WindSurgery == null)
        {
            result.WindSurgery = card.WindSurgery;
            filled++;
        }
        if (card.TrainerRtf != null && result.TrainerRtf == null)
        {
            result.TrainerRtf = card.TrainerRtf;
            filled++;
        }
        if (card.JockeyAllowanceLbs != null && result.JockeyAllowanceLbs == null)
        {
            result.JockeyAllowanceLbs = card.JockeyAllowanceLbs;
            filled++;
        }
        if (card.NewTrainerRacesCount != null && result.NewTrainerRacesCount == null)
        {
            result.NewTrainerRacesCount = card.NewTrainerRacesCount;
            filled++;
        }
        if (!string.IsNullOrEmpty(card.CountryOfOrigin) && string.IsNullOrEmpty(result.CountryOfOrigin))
        {
            result.CountryOfOrigin = card.CountryOfOrigin;
            filled++;
        }
        if (!string.IsNullOrEmpty(card.Spotlight) && string.IsNullOrEmpty(result.Spotlight))
        {
            result.Spotlight = card.Spotlight;
            filled++;
        }

        return filled;
    }

    private static bool StakeReturnedFor(ResultStatus resultStatus) =>
        resultStatus is ResultStatus.RaceVoid or ResultStatus.NonRunner;

    // Degrades gracefully to the flat-£1-per-pick figure when no advised stakes are present, rather than dividing by zero.
    public static double StakeWeightedReturnPercentage(IReadOnlyCollection<RaceCardPredictionScore> scores) =>
        scores.Sum(x => x.Stake ?? 0) > 0
            ? ReturnPercentage(scores, x => x.Stake ?? 0)
            : ReturnPercentage(scores, _ => 1.0);

    // The shared return formula; the flat-£1 figure is just every pick staked at 1 (stakeOf => 1.0).
    private static double ReturnPercentage(IReadOnlyCollection<RaceCardPredictionScore> scores, Func<RaceCardPredictionScore, double> stakeOf)
    {
        var totalStake = scores.Sum(stakeOf);
        if (totalStake <= 0)
        {
            return 0.0;
        }

        var loserStake = scores.Where(x => !x.Won && !StakeReturnedFor(x.ResultStatus)).Sum(stakeOf);
        var returnedStake = scores.Where(x => StakeReturnedFor(x.ResultStatus)).Sum(stakeOf);
        var winnings = scores.Where(x => x.Won).Sum(x => stakeOf(x) * (x.DecimalOdds ?? 0)) + returnedStake;
        return (winnings - loserStake) / totalStake * 100.0;
    }

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
