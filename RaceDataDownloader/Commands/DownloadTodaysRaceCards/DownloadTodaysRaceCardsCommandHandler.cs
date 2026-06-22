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

    // Informational fill-rate datapoint for the per-runner extras (Issue 005). Unlike the forecast and
    // ratings canaries this never warns: the extras are legitimately sparse (first-time flags rarely
    // fire; trainerRtf is absent on some jurisdictions such as HK; wind-surgery is jumps-skewed), so a
    // zero count is normal data, not a structural alarm. The throw on a vanished key is owned by the
    // reader's schema validation, so this canary only ever logs at the information level and never throws.
    private void LogExtrasFillRate(List<RaceCard> raceCards)
    {
        var totalRunners = raceCards.Sum(c => c.Runners.Length);
        if (totalRunners == 0)
        {
            return;
        }

        int Count(Func<RaceRunnerExtras, bool> present) =>
            raceCards.Sum(c => c.Runners.Count(r => r.Extras is not null && present(r.Extras)));

        Logger.LogInformation(
            "Racecard extras present for {Total} runners: headgear-first {HeadgearFirstTime}, gelding-first {GeldingFirstTime}, " +
            "wind-surgery {WindSurgery}, trainerRtf {TrainerRtf}, jockey-allowance {JockeyAllowanceLbs}, jockey-first {JockeyFirstTime}, " +
            "new-trainer-count {NewTrainerRacesCount}, country {CountryOfOrigin}, spotlight {Spotlight}.",
            totalRunners,
            Count(e => e.HeadgearFirstTime.HasValue),
            Count(e => e.GeldingFirstTime.HasValue),
            Count(e => e.WindSurgery.HasValue),
            Count(e => e.TrainerRtf.HasValue),
            Count(e => e.JockeyAllowanceLbs.HasValue),
            Count(e => e.JockeyFirstTime.HasValue),
            Count(e => e.NewTrainerRacesCount.HasValue),
            Count(e => !string.IsNullOrEmpty(e.CountryOfOrigin)),
            Count(e => !string.IsNullOrEmpty(e.Spotlight)));
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
