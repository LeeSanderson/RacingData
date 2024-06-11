namespace RacePredictor.Core.RacingPost;

/// <summary>
/// Table to get average lengths per second values based on course and going.
/// This is then used to calculate the race time of a horse given the winning time and overall beaten distance
/// Based off data here: https://www.britishhorseracing.com/wp-content/uploads/2014/04/Lengths-Per-Second-Scale-Tables-2019.pdf
/// </summary>
internal static class LengthsPerSecondScaleTable
{
    internal static double GetLengthsPerSecondScale(RaceType raceType, string? going, string courseName)
    {
        var isSouthWell = courseName.ToLowerInvariant() == "southwell";
        if (raceType == RaceType.Flat)
        {
            if (string.IsNullOrEmpty(going))
            {
                return 6;
            }

            if (going.ContainsAnyIgnoreCase("firm", "standard", "fast", "hard", "slow", "sloppy"))
            {
                return isSouthWell ? 5 : 6;
            }

            if (going.ContainsAnyIgnoreCase("good"))
            {
                return going.ContainsAnyIgnoreCase("soft", "yielding") ? 5.5 : 6;
            }

            return 5;
        }

        if (string.IsNullOrEmpty(going))
        {
            return 5;
        }

        if (going.ContainsAnyIgnoreCase("firm", "standard", "hard", "fast"))
        {
            return isSouthWell ? 4 : 5;
        }

        if (going.ContainsAnyIgnoreCase("good"))
        {
            return going.ContainsAnyIgnoreCase("soft", "yielding") ? 4.5 : 5;
        }

        return going.ContainsAnyIgnoreCase("soft", "heavy", "yielding", "slow", "holding") ? 4 : 5;
    }
}
