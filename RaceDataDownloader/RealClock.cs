using RacePredictor.Core.RacingPost;

namespace RaceDataDownloader;

internal sealed class RealClock : IClock
{
    public bool IsToday(DateOnly date) => date == Today;

    public bool IsTomorrow(DateOnly date) => date == Today.AddDays(1);

    public DateOnly Today => DateOnly.FromDateTime(DateTime.Today);
}
