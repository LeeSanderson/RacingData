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
            PrizeMoneyValue = 4397m,
            OwnerId = 322703,
            OwnerName = "Li Xiting",
            SireName = "Not A Single Doubt",
            SireCountry = "AUS",
            DamName = "Jacquetta",
            HeadgearFirstTime = true,
            GeldingFirstTime = false,
            WindSurgery = 2,
            TrainerRtf = 59,
            JockeyAllowanceLbs = 5,
            JockeyFirstTime = true,
            NewTrainerRacesCount = 1,
            CountryOfOrigin = "FR",
            Spotlight = "Won well; \"one to note\", strong at C&D"
        };

        var single = (await (await new[] { record }.ToCsvString()).FromCsvString<RaceCardRecord>()).Single();

        single.DaysSinceLastRun.Should().Be(32);
        single.FormFigures.Should().Be("3-1958");
        single.PrizeMoney.Should().Be("£4,397");
        single.PrizeMoneyValue.Should().Be(4397m);
        single.OwnerId.Should().Be(322703);
        single.OwnerName.Should().Be("Li Xiting");
        single.SireName.Should().Be("Not A Single Doubt");
        single.SireCountry.Should().Be("AUS");
        single.DamName.Should().Be("Jacquetta");
        single.HeadgearFirstTime.Should().BeTrue();
        single.GeldingFirstTime.Should().BeFalse();
        single.WindSurgery.Should().Be(2);
        single.TrainerRtf.Should().Be(59);
        single.JockeyAllowanceLbs.Should().Be(5);
        single.JockeyFirstTime.Should().BeTrue();
        single.NewTrainerRacesCount.Should().Be(1);
        single.CountryOfOrigin.Should().Be("FR");
        single.Spotlight.Should().Be("Won well; \"one to note\", strong at C&D");
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
        records[0].OwnerId.Should().BeNull();
        records[0].OwnerName.Should().BeNullOrEmpty();
        records[0].SireName.Should().BeNullOrEmpty();
        records[0].SireCountry.Should().BeNullOrEmpty();
        records[0].DamName.Should().BeNullOrEmpty();
        records[0].HeadgearFirstTime.Should().BeNull();
        records[0].GeldingFirstTime.Should().BeNull();
        records[0].WindSurgery.Should().BeNull();
        records[0].TrainerRtf.Should().BeNull();
        records[0].JockeyAllowanceLbs.Should().BeNull();
        records[0].JockeyFirstTime.Should().BeNull();
        records[0].NewTrainerRacesCount.Should().BeNull();
        records[0].CountryOfOrigin.Should().BeNullOrEmpty();
        records[0].Spotlight.Should().BeNullOrEmpty();
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
        // Owner is captured per-runner; every runner on this card carries one.
        records.Should().OnlyContain(r => r.OwnerId.HasValue && !string.IsNullOrEmpty(r.OwnerName));
        records.Should().Contain(r => r.HorseId == 4043909 && r.OwnerId == 322703 && r.OwnerName == "Li Xiting");
        // Breeding is captured per-runner too; every runner on this card carries a sire and dam.
        records.Should().OnlyContain(r =>
            !string.IsNullOrEmpty(r.SireName) && !string.IsNullOrEmpty(r.SireCountry) && !string.IsNullOrEmpty(r.DamName));
        records.Should().Contain(r =>
            r.HorseId == 4043909 && r.SireName == "Not A Single Doubt" && r.SireCountry == "AUS" && r.DamName == "Jacquetta");
        // Extras are captured per-runner. Every HK runner carries a country of origin and Spotlight prose;
        // the first-time flags are clean falses (none fired) and trainerRtf is a clean null (HK lacks the
        // win-rate badge) — absence is data, not a failure.
        records.Should().OnlyContain(r => !string.IsNullOrEmpty(r.CountryOfOrigin) && !string.IsNullOrEmpty(r.Spotlight));
        records.Should().OnlyContain(r => r.TrainerRtf == null);
        records.Should().Contain(r =>
            r.HorseId == 4043909 && r.CountryOfOrigin == "AUS" && r.HeadgearFirstTime == false &&
            r.GeldingFirstTime == false && r.JockeyFirstTime == false);
        records.Should().Contain(r => r.HorseId == 4043909 && r.Spotlight!.StartsWith("2-41 in Hong Kong"));
    }
}
