namespace RaceDataDownloader.Commands;

internal static class DateRange
{
    public static IEnumerable<(DateOnly monthStart, DateOnly monthEnd)> SplitRangeIntoMonths(DateOnly start, DateOnly end)
    {
        var monthStart = start;
        while (monthStart <= end)
        {
            var monthEnd = new DateOnly(monthStart.Year, monthStart.Month, DateTime.DaysInMonth(monthStart.Year, monthStart.Month));
            monthEnd = monthEnd > end ? end : monthEnd;
            yield return (monthStart, monthEnd);
            monthStart = monthEnd.AddDays(1);
        }
    }
}