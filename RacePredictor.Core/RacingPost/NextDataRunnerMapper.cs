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
            new RaceRunnerStats(new RaceOdds(r.ForecastFractionalOdds ?? "SP"), r.OfficialRating, r.RacingPostRating, r.TopSpeedRating));
}
