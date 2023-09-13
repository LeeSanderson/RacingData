using RaceDataDownloader.Models;
using RacePredictor.Core;

namespace RaceDataDownloader.Commands.PredictTodaysRaceCards;

public class AverageSpeedRaceCardPredictor
{
    private readonly List<GroupedAverageSpeed> _averageSpeeds;

    public AverageSpeedRaceCardPredictor(IEnumerable<RaceResultRecord> historicResults)
    {
        _averageSpeeds = historicResults
            .Where(r => r.ResultStatus == ResultStatus.CompletedRace)
            .GroupBy(r => new { r.HorseId, r.RaceType, r.Going, DistanceType = DistanceTypes.FromDistance(r.DistanceInMeters) })
            .Select(g => new GroupedAverageSpeed
            {
                HorseId = g.Key.HorseId,
                RaceType = g.Key.RaceType,
                DistanceType = g.Key.DistanceType,
                Going = g.Key.Going ?? string.Empty,
                AverageSpeed = g.Sum(x => x.DistanceInMeters) / g.Sum(x => x.RaceTimeInSeconds)
            })
            .ToList();
    }

    public IEnumerable<RaceCardPrediction> PredictRaceCardResults(List<RaceCardRecord> raceCardsToPredict)
    {
        var races = raceCardsToPredict.GroupBy(r => r.RaceId).Select(g => g);
        foreach (var race in races)
        {
            RaceCardRecord? fastestHorseRaceCardRecord = null;
            double fastestHorseAverageSpeed = 0;
            foreach (var runner in race)
            {
                var speed = _averageSpeeds.FirstOrDefault(s =>
                    s.HorseId == runner.HorseId &&
                    s.RaceType == runner.RaceType &&
                    s.Going == runner.Going &&
                    s.DistanceType == DistanceTypes.FromDistance(runner.DistanceInMeters));
                if (speed != null && speed.AverageSpeed > fastestHorseAverageSpeed)
                {
                    fastestHorseRaceCardRecord = runner;
                    fastestHorseAverageSpeed = speed.AverageSpeed;
                }
            }

            if (fastestHorseRaceCardRecord != null)
            {
                yield return new RaceCardPrediction
                {
                    CourseId = fastestHorseRaceCardRecord.CourseId,
                    CourseName = fastestHorseRaceCardRecord.CourseName,
                    RaceId = fastestHorseRaceCardRecord.RaceId,
                    RaceName = fastestHorseRaceCardRecord.RaceName,
                    HorseId = fastestHorseRaceCardRecord.HorseId,
                    HorseName = fastestHorseRaceCardRecord.HorseName,
                    Off = fastestHorseRaceCardRecord.Off
                };
            }
        }
    }
}
