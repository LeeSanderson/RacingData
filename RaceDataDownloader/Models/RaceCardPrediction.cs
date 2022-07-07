namespace RaceDataDownloader.Models;

public class RaceCardPrediction
{
    public int RaceId { get; set; }
    public string RaceName { get; set; } = string.Empty;
    public int CourseId { get; set; }
    public string CourseName { get; set; } = string.Empty;
    public DateTime Off { get; set; }
    public int HorseId { get; set; }
    public string HorseName { get; set; } = string.Empty;
}