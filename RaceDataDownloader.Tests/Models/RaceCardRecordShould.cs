using RaceDataDownloader.Commands;
using RaceDataDownloader.Models;
using RaceDataDownloader.Tests.Fakes;
using RacePredictor.Core.RacingPost;

namespace RaceDataDownloader.Tests.Models;

public class RaceCardRecordShould
{
    [Fact]
    public async Task RoundTripCardDataColumnsThroughCsv()
    {
        var record = new RaceCardRecord
        {
            RaceId = 920859,
            HorseId = 4043909,
            DaysSinceLastRun = 32,
            FormFigures = "3-1958",
            PrizeMoney = "£4,397",
            PrizeMoneyValue = 4397m
        };

        var single = (await (await new[] { record }.ToCsvString()).FromCsvString<RaceCardRecord>()).Single();

        single.DaysSinceLastRun.Should().Be(32);
        single.FormFigures.Should().Be("3-1958");
        single.PrizeMoney.Should().Be("£4,397");
        single.PrizeMoneyValue.Should().Be(4397m);
    }

    [Fact]
    public async Task TolerateALegacyCsvMissingThePreRaceColumns()
    {
        const string legacyCsv =
            "RaceId,RaceName,CourseId,CourseName,Off,RaceType,Class,Pattern,RatingBand,AgeBand,SexRestriction," +
            "Distance,DistanceInFurlongs,DistanceInMeters,DistanceInYards,Going,Surface," +
            "HorseId,HorseName,JockeyId,JockeyName,TrainerId,TrainerName,Age,HeadGear," +
            "RaceCardNumber,StallNumber,Weight,WeightInPounds,FractionalOdds,DecimalOdds," +
            "OfficialRating,RacingPostRating,TopSpeedRating\r\n" +
            "921202,Test Race,174,Newmarket (July),06/20/2026 13:24:00,Other,Class 5,,0-70,4yo+,None," +
            "1m,8,1608,1760,Good To Firm,Turf,8052952,Freddie's Star IRE,99143,Owen Lewis (5)," +
            "19203,Roger Teal,4,,1,8,9-12,156,16/1,17,70,78,29\r\n";

        var records = await legacyCsv.FromCsvString<RaceCardRecord>();

        records.Should().HaveCount(1);
        records[0].RaceId.Should().Be(921202);
        records[0].TopSpeedRating.Should().Be(29);
        records[0].DaysSinceLastRun.Should().BeNull();
        records[0].FormFigures.Should().BeNullOrEmpty();
        records[0].PrizeMoney.Should().BeNullOrEmpty();
        records[0].PrizeMoneyValue.Should().BeNull();
    }

    [Fact]
    public async Task SurfaceTheParsedPreRaceFieldsFromTheRaceCard()
    {
        var raceCard = await new RaceCardParser().Parse(FakeData.HappyValleyRaceCardFor1140RaceOn20260520);

        var records = RaceCardRecord.ListFrom(raceCard).ToList();

        records.Should().NotBeEmpty();
        // Days-since and form are per-runner; at least one runner on a real card carries them.
        records.Should().Contain(r => r.DaysSinceLastRun.HasValue);
        records.Should().Contain(r => !string.IsNullOrEmpty(r.FormFigures));
        // Prize money is race-level, so every record on this single-race fixture shares it.
        records.Should().OnlyContain(r => !string.IsNullOrEmpty(r.PrizeMoney));
        records.Should().OnlyContain(r => r.PrizeMoneyValue.HasValue);
    }
}
