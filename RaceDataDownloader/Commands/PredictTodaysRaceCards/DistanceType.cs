namespace RaceDataDownloader.Commands.PredictTodaysRaceCards;

public enum DistanceType
{
    VeryShort,
    Short,
    Medium,
    Long,
    VeryLong
}

public static class DistanceTypes
{
    public static DistanceType FromDistance(int distanceInMeters) =>
        distanceInMeters switch
        {
            < 1300 => DistanceType.VeryShort,
            < 1700 => DistanceType.Short,
            < 3000 => DistanceType.Medium,
            < 4000 => DistanceType.Long,
            _ => DistanceType.VeryLong
        };
}