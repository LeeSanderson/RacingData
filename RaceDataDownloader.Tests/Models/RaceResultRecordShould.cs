using RaceDataDownloader.Commands;
using RaceDataDownloader.Models;

namespace RaceDataDownloader.Tests.Models;

public class RaceResultRecordShould
{
    [Fact]
    public async Task LoadLegacyResultsCsvWithoutForecastColumns()
    {
        // A legacy Results_YYYYMM.csv predates the Forecast* columns: it carries only
        // the original 40 columns (Index 0-39). Build one faithfully by serialising a
        // record and dropping the two new trailing columns, then prove it still loads.
        var record = new RaceResultRecord
        {
            RaceId = 809925,
            RaceName = "Some Handicap",
            HorseId = 3116615,
            HorseName = "Amasova",
            FractionalOdds = "13/2",
            DecimalOdds = 7.5
        };
        var legacyCsv = StripLastColumns(await new[] { record }.ToCsvString(), 2);

        var loaded = await legacyCsv.FromCsvString<RaceResultRecord>();

        var single = loaded.Single();
        single.HorseId.Should().Be(3116615);              // positional mapping still aligned
        single.DecimalOdds.Should().Be(7.5);              // last pre-existing columns unaffected
        single.ForecastFractionalOdds.Should().BeNullOrEmpty();
        single.ForecastDecimalOdds.Should().BeNull();
    }

    [Fact]
    public async Task RoundTripForecastOddsThroughCsv()
    {
        var record = new RaceResultRecord
        {
            RaceId = 809925,
            HorseId = 3116615,
            FractionalOdds = "13/2",   // post-race SP, unchanged meaning
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

    private static string StripLastColumns(string csv, int count)
    {
        var lines = csv.Replace("\r\n", "\n").TrimEnd('\n').Split('\n');
        var stripped = lines.Select(line => string.Join(',', line.Split(',')[..^count]));
        return string.Join("\r\n", stripped) + "\r\n";
    }
}
