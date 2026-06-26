using System.ComponentModel.DataAnnotations;
using RacePredictor.Core;
using RacePredictor.Core.RacingPost;

namespace RacePredictor.Core.Tests.RacingPost;

public class RaceCardRunnerCrossValidatorShould
{
    [Fact]
    public void NotThrowWhenJsonAndDomAgreeOnEveryOverlappingField()
    {
        var json = Card(5);
        var dom = Card(5);

        var validate = () => RaceCardRunnerCrossValidator.Validate(json, dom);

        validate.Should().NotThrow();
    }

    [Fact]
    public void NotThrowWhenASingleRunnerDivergesWithinTolerance()
    {
        // One non-runner-style edge across an otherwise-agreeing card is benign and must not abort.
        var json = Card(5);
        var dom = Card(5);
        dom[2] = With(dom[2], form: "9999");

        var validate = () => RaceCardRunnerCrossValidator.Validate(json, dom);

        validate.Should().NotThrow();
    }

    [Fact]
    public void ThrowNamingTheFieldWhenDivergenceIsSystematic()
    {
        // Every runner disagrees on form figures: the JSON node being read no longer corresponds
        // to the rendered card.
        var json = Card(4);
        var dom = Card(4).Select(r => With(r, form: r.Attributes.FormFigures + "X")).ToList();

        var validate = () => RaceCardRunnerCrossValidator.Validate(json, dom);

        validate.Should().Throw<ValidationException>().WithMessage("*FormFigures*");
    }

    [Fact]
    public void ThrowWhenTheJsonRunnerSetDoesNotCorrespondToTheRenderedCard()
    {
        // None of the DOM runners has a matching JSON runner by horse id.
        var dom = Card(4);
        var json = Card(4).Select(r => With(r, horseId: r.Horse.Id + 1000)).ToList();

        var validate = () => RaceCardRunnerCrossValidator.Validate(json, dom);

        validate.Should().Throw<ValidationException>().WithMessage("*correspond*");
    }

    [Fact]
    public void NotThrowWhenThereIsNoDomOracleReadingToCompareAgainst()
    {
        var json = Card(5);

        var validate = () => RaceCardRunnerCrossValidator.Validate(json, new List<RaceRunner>());

        validate.Should().NotThrow();
    }

    [Fact]
    public void NotThrowOnForecastOddsWhenTheDomRendersNoForecast()
    {
        // Arabian (ARO) cards carry a betting forecast in the JSON island but render no forecast
        // section, so the oracle reads SP for every runner. Absence in the oracle cannot contradict
        // the JSON, so it is not divergence.
        var json = Card(4);
        var dom = Card(4).Select(r => With(r, odds: new RaceOdds("SP"))).ToList();

        var validate = () => RaceCardRunnerCrossValidator.Validate(json, dom);

        validate.Should().NotThrow();
    }

    [Fact]
    public void ThrowOnForecastOddsWhenADomRenderedPriceContradictsTheJson()
    {
        // The DOM renders a real price for every runner that the JSON disagrees with: a regressed
        // JSON forecast capture must still be caught.
        var json = Card(4).Select(r => With(r, odds: new RaceOdds("SP"))).ToList();
        var dom = Card(4);

        var validate = () => RaceCardRunnerCrossValidator.Validate(json, dom);

        validate.Should().Throw<ValidationException>().WithMessage("*ForecastOdds*");
    }

    private static List<RaceRunner> Card(int count) =>
        Enumerable.Range(1, count).Select(BuildRunner).ToList();

    private static RaceRunner BuildRunner(int i) =>
        new(
            new RaceEntity(1000 + i, $"Horse {i}"),
            new RaceEntity(2000 + i, $"Jockey {i}"),
            new RaceEntity(3000 + i, $"Trainer {i}"),
            new RaceRunnerAttributes(i, i, 5, new RaceWeight(9, 7), null, 14, $"{i}1-2"),
            new RaceRunnerStats(new RaceOdds("5/1"), 60, 70, 50));

    private static RaceRunner With(RaceRunner r, int? horseId = null, string? form = null, RaceOdds? odds = null) =>
        new(
            new RaceEntity(horseId ?? r.Horse.Id, r.Horse.Name),
            r.Jockey,
            r.Trainer,
            new RaceRunnerAttributes(
                r.Attributes.RaceCardNumber, r.Attributes.StallNumber, r.Attributes.Age, r.Attributes.Weight,
                r.Attributes.HeadGear, r.Attributes.DaysSinceLastRun, form ?? r.Attributes.FormFigures),
            odds is null
                ? r.Statistics
                : new RaceRunnerStats(odds, r.Statistics.OfficialRating, r.Statistics.RacingPostRating, r.Statistics.TopSpeedRating));
}
