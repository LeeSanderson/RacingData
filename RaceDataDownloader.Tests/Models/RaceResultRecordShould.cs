using RaceDataDownloader.Commands;
using RaceDataDownloader.Models;

namespace RaceDataDownloader.Tests.Models;

public class RaceResultRecordShould
{
    [Fact]
    public async Task LoadLegacyResultsCsvWithoutForecastOrCardColumns()
    {
        // Simulate an original results file written before the Forecast*/card-data columns existed by
        // serialising a record and dropping those new trailing columns.
        var record = new RaceResultRecord
        {
            RaceId = 809925,
            RaceName = "Some Handicap",
            HorseId = 3116615,
            HorseName = "Amasova",
            FractionalOdds = "13/2",
            DecimalOdds = 7.5
        };
        var legacyCsv = StripLastColumns(await new[] { record }.ToCsvString(), 9);

        var loaded = await legacyCsv.FromCsvString<RaceResultRecord>();

        var single = loaded.Single();
        single.HorseId.Should().Be(3116615);
        single.DecimalOdds.Should().Be(7.5);
        single.ForecastFractionalOdds.Should().BeNullOrEmpty();
        single.ForecastDecimalOdds.Should().BeNull();
        single.DaysSinceLastRun.Should().BeNull();
        single.FormFigures.Should().BeNullOrEmpty();
        single.PrizeMoney.Should().BeNullOrEmpty();
        single.PrizeMoneyValue.Should().BeNull();
        single.CardOfficialRating.Should().BeNull();
        single.CardRacingPostRating.Should().BeNull();
        single.CardTopSpeedRating.Should().BeNull();
    }

    [Fact]
    public async Task LoadResultsCsvWithForecastButWithoutCardColumns()
    {
        // The realistic upgrade path: an intermediate-schema file written after Forecast* shipped but
        // before the card-data columns. Dropping the card columns must still load, with forecast preserved.
        var record = new RaceResultRecord
        {
            RaceId = 809925,
            HorseId = 3116615,
            FractionalOdds = "13/2",
            DecimalOdds = 7.5,
            ForecastFractionalOdds = "11/2",
            ForecastDecimalOdds = 6.5
        };
        var csv = StripLastColumns(await new[] { record }.ToCsvString(), 7);

        var single = (await csv.FromCsvString<RaceResultRecord>()).Single();

        single.ForecastFractionalOdds.Should().Be("11/2");
        single.ForecastDecimalOdds.Should().Be(6.5);
        single.DaysSinceLastRun.Should().BeNull();
        single.CardOfficialRating.Should().BeNull();
    }

    [Fact]
    public async Task RoundTripForecastOddsThroughCsv()
    {
        var record = new RaceResultRecord
        {
            RaceId = 809925,
            HorseId = 3116615,
            FractionalOdds = "13/2",
            DecimalOdds = 7.5,
            ForecastFractionalOdds = "11/2",
            ForecastDecimalOdds = 6.5
        };

        var loaded = await (await new[] { record }.ToCsvString()).FromCsvString<RaceResultRecord>();

        var single = loaded.Single();
        single.FractionalOdds.Should().Be("13/2");
        single.DecimalOdds.Should().Be(7.5);
        single.ForecastFractionalOdds.Should().Be("11/2");
        single.ForecastDecimalOdds.Should().Be(6.5);
    }

    [Fact]
    public async Task RoundTripCardDataColumnsThroughCsv()
    {
        // Guards the index layout: the forwarded card fields sit at high indices on the results layout
        // and the Card* ratings follow. A collision or gap would silently read back a neighbour's value,
        // so assert every column survives the round trip distinctly.
        var record = new RaceResultRecord
        {
            RaceId = 809925,
            HorseId = 3116615,
            FractionalOdds = "13/2",
            DecimalOdds = 7.5,
            ForecastFractionalOdds = "11/2",
            ForecastDecimalOdds = 6.5,
            DaysSinceLastRun = 32,
            FormFigures = "3-1958",
            PrizeMoney = "£4,397",
            PrizeMoneyValue = 4397m,
            CardOfficialRating = 88,
            CardRacingPostRating = 91,
            CardTopSpeedRating = 77
        };

        var single = (await (await new[] { record }.ToCsvString()).FromCsvString<RaceResultRecord>()).Single();

        single.ForecastDecimalOdds.Should().Be(6.5);
        single.DaysSinceLastRun.Should().Be(32);
        single.FormFigures.Should().Be("3-1958");
        single.PrizeMoney.Should().Be("£4,397");
        single.PrizeMoneyValue.Should().Be(4397m);
        single.CardOfficialRating.Should().Be(88);
        single.CardRacingPostRating.Should().Be(91);
        single.CardTopSpeedRating.Should().Be(77);
    }

    [Fact]
    public async Task RoundTripOwnerBreedingAndExtrasColumnsThroughCsv()
    {
        // Guards the high end of the results layout (indices 49-62) that no other test exercises: owner,
        // breeding and the nine per-runner extras. A collision or off-by-one at these indices would read
        // back a neighbour's value, so assert every column survives the round trip distinctly. GeldingFirstTime
        // is set to false to confirm a captured false stays false (not null) through the CSV round trip.
        var record = new RaceResultRecord
        {
            RaceId = 809925,
            HorseId = 3116615,
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

        var single = (await (await new[] { record }.ToCsvString()).FromCsvString<RaceResultRecord>()).Single();

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

    private static string StripLastColumns(string csv, int count)
    {
        var lines = csv.Replace("\r\n", "\n").TrimEnd('\n').Split('\n');
        var stripped = lines.Select(line => string.Join(',', line.Split(',')[..^count]));
        return string.Join("\r\n", stripped) + "\r\n";
    }
}
