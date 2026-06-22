namespace RacePredictor.Core.RacingPost;

/// <summary>
/// Builds the captured <see cref="RaceRunner"/> list from the validated <c>__NEXT_DATA__</c> view.
/// Non-runners and reserves are dropped (matching the DOM parser), and the active runners are ordered
/// by race-card number so the emitted CSV matches the rendered card order.
/// </summary>
internal static class NextDataRunnerMapper
{
    public static RaceRunner[] ToRaceRunners(NextDataRaceCardView view) =>
        view.Runners
            .Where(r => !r.IsNonRunner)
            .OrderBy(r => r.RaceCardNumber)
            .ThenBy(r => r.HorseId ?? 0)
            .Select(ToRaceRunner)
            .ToArray();

    private static RaceRunner ToRaceRunner(NextDataRunner r) =>
        new(
            new RaceEntity(r.HorseId ?? 0, r.HorseName ?? string.Empty),
            new RaceEntity(r.JockeyId ?? 0, r.JockeyName ?? "Unknown Jockey"),
            new RaceEntity(r.TrainerId ?? 0, r.TrainerName ?? "Unknown Trainer"),
            new RaceRunnerAttributes(r.RaceCardNumber, r.Draw, r.Age, r.Weight, r.HeadGear, r.DaysSinceLastRun, r.FormFigures),
            new RaceRunnerStats(new RaceOdds(r.ForecastFractionalOdds ?? "SP"), r.OfficialRating, r.RacingPostRating, r.TopSpeedRating),
            ToOwner(r),
            ToBreeding(r),
            ToExtras(r));

    // Owner is the one new field that is also backfill-able: it appears on daily result pages, unlike
    // breeding/verdict/wind-op. A historic-results re-scrape could fold ownerId/ownerName in alongside
    // form / days-since / prize money -- see issues/todo.md "Backfill form / days-since / prize money
    // into historic Results". Recorded only; no historic backfill is performed here.
    // A present-but-null owner (id and name both absent) stays a clean null rather than a 0/empty entity.
    private static RaceEntity? ToOwner(NextDataRunner r) =>
        r.OwnerId is null && r.OwnerName is null
            ? null
            : new RaceEntity(r.OwnerId ?? 0, r.OwnerName ?? string.Empty);

    // Breeding is forward-only and NOT backfill-able (absent from result pages). When every breeding
    // field is absent the runner carries a clean null rather than an all-null value object.
    private static RaceRunnerBreeding? ToBreeding(NextDataRunner r) =>
        r.SireName is null && r.SireCountry is null && r.DamName is null
            ? null
            : new RaceRunnerBreeding(r.SireName, r.SireCountry, r.DamName);

    // Extras are forward-only and NOT backfill-able (absent from result pages). When every extra field
    // is absent the runner carries a clean null rather than an all-null value object. In practice
    // CountryOfOrigin is present for nearly every runner, so this null guard rarely fires.
    private static RaceRunnerExtras? ToExtras(NextDataRunner r) =>
        r.HeadgearFirstTime is null && r.GeldingFirstTime is null && r.WindSurgery is null &&
        r.TrainerRtf is null && r.JockeyAllowanceLbs is null && r.JockeyFirstTime is null &&
        r.NewTrainerRacesCount is null && r.CountryOfOrigin is null && r.Spotlight is null
            ? null
            : new RaceRunnerExtras(
                r.HeadgearFirstTime, r.GeldingFirstTime, r.WindSurgery, r.TrainerRtf,
                r.JockeyAllowanceLbs, r.JockeyFirstTime, r.NewTrainerRacesCount, r.CountryOfOrigin, r.Spotlight);
}
