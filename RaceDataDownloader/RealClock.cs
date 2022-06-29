using RacePredictor.Core.RacingPost;

namespace RaceDataDownloader
{
    internal class RealClock : IClock
    {
        public bool IsToday(DateOnly date) => date == Today;

        public bool IsTomorrow(DateOnly date) => date == Today.AddDays(1);

        public DateOnly Today => DateOnly.FromDateTime(DateTime.Today);
    }
}
