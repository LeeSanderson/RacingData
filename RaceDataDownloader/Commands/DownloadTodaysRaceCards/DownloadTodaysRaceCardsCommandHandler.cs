using System.ComponentModel.DataAnnotations;
using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using RaceDataDownloader.Models;
using RacePredictor.Core;
using RacePredictor.Core.RacingPost;

namespace RaceDataDownloader.Commands.DownloadTodaysRaceCards;

public class DownloadTodaysRaceCardsCommandHandler(
    IFileSystem fileSystem,
    IRacingDataDownloader downloader,
    IClock clock,
    ILogger<DownloadTodaysRaceCardsCommandHandler> logger)
    : FileCommandHandlerBase<DownloadTodaysRaceCardsCommandHandler, DownloadTodaysRaceCardsOptions>(fileSystem, logger)
{
    protected override async Task InternalRunAsync(DownloadTodaysRaceCardsOptions options)
    {
        var dataFolder = ValidateAndCreateOutputFolder(options.DataDirectory);
        var today = clock.Today;

        var raceResults = await downloader.DownloadRaceCardsInDateRange(Logger, today, today);

        EnsureGoingDataIsPresent(raceResults);
        LogForecastFillRate(raceResults);
        LogRatingsFillRate(raceResults);
        LogExtrasFillRate(raceResults);

        await FileSystem.WriteRecordsToCsvFile(
            Path.Combine(dataFolder, "TodaysRaceCards.csv"),
            raceResults.SelectMany(RaceCardRecord.ListFrom));
    }

    // Soft canary for a Racing Post betting-forecast markup change: log how many runners got a forecast
    // and warn (never throw) when a non-empty card yields none. A non-null DecimalOdds marks a real
    // forecast; runners left at the "SP" default don't count -- same predicate the validate merge uses.
    private void LogForecastFillRate(List<RaceCard> raceCards)
    {
        var totalRunners = raceCards.Sum(c => c.Runners.Length);
        if (totalRunners == 0)
        {
            return;
        }

        var withForecast = raceCards.Sum(c => c.Runners.Count(r => r.Statistics.Odds.DecimalOdds.HasValue));
        Logger.LogInformation("Forecast odds present for {WithForecast} of {Total} runners.", withForecast, totalRunners);

        if (withForecast == 0)
        {
            Logger.LogWarning(
                "No runners across the {CardCount} downloaded race card(s) have forecast odds. " +
                "The Racing Post betting-forecast structure may have changed.",
                raceCards.Count);
        }
    }

    // Soft canary for a Racing Post runner-stats markup change, mirroring the forecast fill-rate log:
    // count how many runners carry each pre-race rating (the Card* source for the results write-back)
    // and warn (never throw) when a non-empty card yields none of a field. Absence on individual
    // runners is normal (unrated races), so only a whole-field shortfall is worth a warning.
    private void LogRatingsFillRate(List<RaceCard> raceCards)
    {
        var totalRunners = raceCards.Sum(c => c.Runners.Length);
        if (totalRunners == 0)
        {
            return;
        }

        var withOfficialRating = raceCards.Sum(c => c.Runners.Count(r => r.Statistics.OfficialRating.HasValue));
        var withRacingPostRating = raceCards.Sum(c => c.Runners.Count(r => r.Statistics.RacingPostRating.HasValue));
        var withTopSpeedRating = raceCards.Sum(c => c.Runners.Count(r => r.Statistics.TopSpeedRating.HasValue));
        Logger.LogInformation(
            "Pre-race ratings present for {Total} runners: OR {OfficialRating}, RPR {RacingPostRating}, TSR {TopSpeedRating}.",
            totalRunners,
            withOfficialRating,
            withRacingPostRating,
            withTopSpeedRating);

        WarnWhenRatingAbsent(withOfficialRating, "official ratings (OR)", raceCards.Count);
        WarnWhenRatingAbsent(withRacingPostRating, "Racing Post ratings (RPR)", raceCards.Count);
        WarnWhenRatingAbsent(withTopSpeedRating, "top speed ratings (TSR)", raceCards.Count);
    }

    // The extras split by whether a zero count is possible in normal data. The always-present group
    // (the three first-time flags and country of origin) is published for every runner on every
    // jurisdiction's card, so a whole-field shortfall means the JSON stopped carrying it — a structure
    // change, which throws. The rest are legitimately sparse: trainerRtf is absent outside GB/IRE,
    // wind-surgery is jumps-skewed, jockey allowance only appears on claimers, and new-trainer count
    // only after a yard switch. Those are logged and never throw.
    private void LogExtrasFillRate(List<RaceCard> raceCards)
    {
        var totalRunners = raceCards.Sum(c => c.Runners.Length);
        if (totalRunners == 0)
        {
            return;
        }

        int Count(Func<RaceRunnerExtras, bool> present) =>
            raceCards.Sum(c => c.Runners.Count(r => r.Extras is not null && present(r.Extras)));

        var headgearFirstTime = Count(e => e.HeadgearFirstTime.HasValue);
        var geldingFirstTime = Count(e => e.GeldingFirstTime.HasValue);
        var jockeyFirstTime = Count(e => e.JockeyFirstTime.HasValue);
        var countryOfOrigin = Count(e => !string.IsNullOrEmpty(e.CountryOfOrigin));

        Logger.LogInformation(
            "Racecard extras present for {Total} runners: headgear-first {HeadgearFirstTime}, gelding-first {GeldingFirstTime}, " +
            "wind-surgery {WindSurgery}, trainerRtf {TrainerRtf}, jockey-allowance {JockeyAllowanceLbs}, jockey-first {JockeyFirstTime}, " +
            "new-trainer-count {NewTrainerRacesCount}, country {CountryOfOrigin}.",
            totalRunners,
            headgearFirstTime,
            geldingFirstTime,
            Count(e => e.WindSurgery.HasValue),
            Count(e => e.TrainerRtf.HasValue),
            Count(e => e.JockeyAllowanceLbs.HasValue),
            jockeyFirstTime,
            Count(e => e.NewTrainerRacesCount.HasValue),
            countryOfOrigin);

        EnsureAlwaysPresentExtrasArePresent(
            raceCards.Count,
            ("first-time headgear flags", headgearFirstTime),
            ("first-time gelding flags", geldingFirstTime),
            ("first-time jockey flags", jockeyFirstTime),
            ("country of origin", countryOfOrigin));
    }

    // Reports every absent field in one message rather than the first, so a site change that drops
    // several at once is diagnosed from a single run.
    private static void EnsureAlwaysPresentExtrasArePresent(int cardCount, params (string Label, int Count)[] extras)
    {
        var absent = extras.Where(e => e.Count == 0).Select(e => e.Label).ToArray();
        if (absent.Length == 0)
        {
            return;
        }

        throw new ValidationException(
            $"No runners across the {cardCount} downloaded race card(s) have {string.Join(", ", absent)}. " +
            "The Racing Post racecard JSON may have stopped publishing these fields.");
    }

    private void WarnWhenRatingAbsent(int withRating, string ratingLabel, int cardCount)
    {
        if (withRating == 0)
        {
            Logger.LogWarning(
                "No runners across the {CardCount} downloaded race card(s) have {RatingLabel}. " +
                "The Racing Post runner-stats structure may have changed.",
                cardCount,
                ratingLabel);
        }
    }

    private static void EnsureGoingDataIsPresent(List<RaceCard> raceCards)
    {
        if (raceCards.Count > 0 && raceCards.All(r => string.IsNullOrEmpty(r.Attributes.Going)))
        {
            throw new ValidationException(
                $"None of the {raceCards.Count} downloaded race cards has going information. " +
                "The Racing Post page structure may have changed.");
        }
    }
}
