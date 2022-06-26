using RacePredictor.Core.RacingPost;

namespace RaceDataDownloader
{
    internal class RealClock : IClock
    {
        public bool IsToday(DateOnly date) => date == DateOnly.FromDateTime(DateTime.Today);

        public bool IsTomorrow(DateOnly date) => date == DateOnly.FromDateTime(DateTime.Today.AddDays(1));
    }
}
