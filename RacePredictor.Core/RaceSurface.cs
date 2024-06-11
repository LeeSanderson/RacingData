namespace RacePredictor.Core;

public enum RaceSurface
{
    Unknown,
    AllWeather,
    Dirt,
    Turf,
}

public static class RaceSurfaceExtensions
{
    private static readonly Dictionary<string, RaceSurface> StringToSurfaceMap = new(StringComparer.OrdinalIgnoreCase)
    {
        {"Slow", RaceSurface.AllWeather},
        {"Standard", RaceSurface.AllWeather},
        {"Standard To Fast", RaceSurface.AllWeather},
        {"Standard To Slow", RaceSurface.AllWeather},

        {"Fast", RaceSurface.Dirt},
        {"Muddy", RaceSurface.Dirt},
        {"Sloppy", RaceSurface.Dirt},

        {"Firm", RaceSurface.Turf},
        {"Good", RaceSurface.Turf},
        {"Good To Firm", RaceSurface.Turf},
        {"Good To Soft", RaceSurface.Turf},
        {"Good To Yielding", RaceSurface.Turf},
        {"Hard", RaceSurface.Turf},
        {"Heavy", RaceSurface.Turf},
        {"Holding", RaceSurface.Turf},
        {"Soft", RaceSurface.Turf},
        {"Soft To Heavy", RaceSurface.Turf},
        {"Very Soft", RaceSurface.Turf},
        {"Yielding", RaceSurface.Turf},
        {"Yielding To Soft", RaceSurface.Turf},
    };

    public static RaceSurface ToRaceSurface(this string? s) =>
        !string.IsNullOrEmpty(s) && StringToSurfaceMap.TryGetValue(s, out var surface) ? surface: RaceSurface.Unknown;
}
