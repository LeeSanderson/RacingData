namespace RacePredictor.Core.RacingPost;

/// <summary>
/// A typed, read-only view over the per-runner data carried in a race card's <c>__NEXT_DATA__</c>
/// JSON island, plus race-level identity. Produced by <see cref="NextDataRaceCardReader"/>; this
/// slice exposes only the fields the DOM <c>RaceCardRunnerParser</c> already produces.
/// </summary>
public sealed class NextDataRaceCardView
{
    private readonly IReadOnlyDictionary<int, NextDataRunner> _byHorseId;

    internal NextDataRaceCardView(int courseId, int raceId, string raceCountryCode, IReadOnlyList<NextDataRunner> runners)
    {
        CourseId = courseId;
        RaceId = raceId;
        RaceCountryCode = raceCountryCode;
        Runners = runners;
        _byHorseId = runners
            .Where(r => r.HorseId.HasValue)
            .GroupBy(r => r.HorseId!.Value)
            .ToDictionary(g => g.Key, g => g.First());
    }

    public int CourseId { get; }
    public int RaceId { get; }
    public string RaceCountryCode { get; }

    /// <summary>Every entry in the runners array, including non-runners and reserves.</summary>
    public IReadOnlyList<NextDataRunner> Runners { get; }

    public NextDataRunner? RunnerByHorseId(int horseId) =>
        _byHorseId.TryGetValue(horseId, out var runner) ? runner : null;
}

/// <summary>A single runner's overlapping (already-captured) fields, read from <c>__NEXT_DATA__</c>.</summary>
public sealed class NextDataRunner
{
    internal NextDataRunner(
        int? horseId,
        string? horseName,
        int? jockeyId,
        string? jockeyName,
        int? trainerId,
        string? trainerName,
        int age,
        RaceWeight weight,
        int raceCardNumber,
        int? draw,
        int? daysSinceLastRun,
        string? formFigures,
        int? officialRating,
        int? racingPostRating,
        int? topSpeedRating,
        string? headGear,
        string? forecastFractionalOdds,
        double? forecastDecimalOdds,
        bool isNonRunner)
    {
        HorseId = horseId;
        HorseName = horseName;
        JockeyId = jockeyId;
        JockeyName = jockeyName;
        TrainerId = trainerId;
        TrainerName = trainerName;
        Age = age;
        Weight = weight;
        RaceCardNumber = raceCardNumber;
        Draw = draw;
        DaysSinceLastRun = daysSinceLastRun;
        FormFigures = formFigures;
        OfficialRating = officialRating;
        RacingPostRating = racingPostRating;
        TopSpeedRating = topSpeedRating;
        HeadGear = headGear;
        ForecastFractionalOdds = forecastFractionalOdds;
        ForecastDecimalOdds = forecastDecimalOdds;
        IsNonRunner = isNonRunner;
    }

    public int? HorseId { get; }
    public string? HorseName { get; }
    public int? JockeyId { get; }
    public string? JockeyName { get; }
    public int? TrainerId { get; }
    public string? TrainerName { get; }
    public int Age { get; }
    public RaceWeight Weight { get; }
    public int RaceCardNumber { get; }
    public int? Draw { get; }
    public int? DaysSinceLastRun { get; }
    public string? FormFigures { get; }
    public int? OfficialRating { get; }
    public int? RacingPostRating { get; }
    public int? TopSpeedRating { get; }

    /// <summary>The static headgear code (e.g. "t", "tb"); null when the runner wears none.</summary>
    public string? HeadGear { get; }

    /// <summary>The betting-forecast price as a fractional string (e.g. "11/2"); null when the runner has no forecast.</summary>
    public string? ForecastFractionalOdds { get; }

    public double? ForecastDecimalOdds { get; }

    /// <summary>True when the runner is a declared non-runner or reserve (excluded by the DOM parser).</summary>
    public bool IsNonRunner { get; }
}
