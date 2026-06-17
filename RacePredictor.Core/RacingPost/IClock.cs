namespace RacePredictor.Core.RacingPost;

public interface IClock
{
    bool IsToday(DateOnly date);

    bool IsTomorrow(DateOnly date);

    DateOnly Today { get;  }
}