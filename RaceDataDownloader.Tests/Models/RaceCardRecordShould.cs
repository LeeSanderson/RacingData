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
