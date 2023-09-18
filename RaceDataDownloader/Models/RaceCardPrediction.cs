namespace RaceDataDownloader.Models;

public class RaceCardPrediction
{
    public int RaceId { get; set; }
    public int CourseId { get; set; }
    public string CourseName { get; set; } = string.Empty;
    public DateTime Off { get; set; }
    public int HorseId { get; set; }
    public string HorseName { get; set; } = string.Empty;
}
