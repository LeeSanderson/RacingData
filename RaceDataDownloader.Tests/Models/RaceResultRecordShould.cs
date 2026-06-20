using RaceDataDownloader.Commands;
using RaceDataDownloader.Models;

namespace RaceDataDownloader.Tests.Models;

public class RaceResultRecordShould
{
    [Fact]
    public async Task LoadLegacyResultsCsvWithoutForecastOrCardColumns()
    {
        // Simulate the original 40-column file (no Forecast*, no card-data columns) by serialising a
        // record and dropping the nine new trailing columns (Forecast* + the four base card fields +
        // the three Card* ratings).
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
        // The realistic upgrade path: a 42-column file written after Forecast* shipped but before the
        // card-data columns. Dropping the seven card columns must still load, with forecast preserved.
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
        // Guards the index layout: the base card fields are shadowed onto the results layout at high
        // indices and the Card* ratings follow. A collision or gap would silently read back a
        // neighbour's value, so assert every column survives the round trip distinctly.
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

    private static string StripLastColumns(string csv, int count)
    {
        var lines = csv.Replace("\r\n", "\n").TrimEnd('\n').Split('\n');
        var stripped = lines.Select(line => string.Join(',', line.Split(',')[..^count]));
        return string.Join("\r\n", stripped) + "\r\n";
    }
}
