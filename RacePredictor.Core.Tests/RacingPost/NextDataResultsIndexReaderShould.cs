using System.ComponentModel.DataAnnotations;
using RacePredictor.Core.RacingPost;

namespace RacePredictor.Core.Tests.RacingPost;

public class NextDataResultsIndexReaderShould
{
    private static string WrapScript(string scriptContent) =>
        $"<html><head></head><body><script id=\"__NEXT_DATA__\" type=\"application/json\">{scriptContent}</script></body></html>";

    private static string WrapDocument(string resultsJson) =>
        WrapScript("{\"props\":{\"pageProps\":{\"initialState\":{\"results\":" + resultsJson + "}}}}");

    [Fact]
    public void ReturnEveryRaceResultLinkForADayOfRacing()
    {
        var html = ResourceLoader.ReadRacingPostExampleResource("daily_results_20220511.html");

        var links = new NextDataResultsIndexReader().Read(html);

        links.Count.Should().Be(55);
        links[0].Should().Be("/results/5/bath/2022-05-11/809925");
        links.Should().OnlyHaveUniqueItems();
    }

    [Fact]
    public void ExcludeSpecialMeetingsThatRepeatRacesListedUnderTheirOwnCourse()
    {
        var html = ResourceLoader.ReadRacingPostExampleResource("daily_results_20220511.html");

        var links = new NextDataResultsIndexReader().Read(html);

        links.Should().NotContain(link => link.Contains("world-wide-stakes"));
        links.Should().AllSatisfy(link => link.Should().NotStartWith("/results/-"));
    }

    [Fact]
    public void ReturnNoLinksForADayWithoutRacing()
    {
        var html = ResourceLoader.ReadRacingPostExampleResource("daily_results_20251225_no_racing.html");

        var links = new NextDataResultsIndexReader().Read(html);

        links.Should().BeEmpty();
    }

    [Fact]
    public void ThrowWhenNoResultsArePresentAndThePageDoesNotSayWhy()
    {
        var read = () => new NextDataResultsIndexReader().Read(WrapDocument("{\"data\":null}"));

        read.Should().Throw<ValidationException>().WithMessage("*no results for this date*");
    }

    [Fact]
    public void ThrowWhenTheResultsSliceIsMissing()
    {
        var read = () => new NextDataResultsIndexReader()
            .Read(WrapScript("{\"props\":{\"pageProps\":{\"initialState\":{}}}}"));

        read.Should().Throw<ValidationException>().WithMessage("*results*");
    }

    [Fact]
    public void ThrowWhenAMeetingIsMissingItsSpecialMeetingFlag()
    {
        var read = () => new NextDataResultsIndexReader()
            .Read(WrapDocument("{\"data\":[{\"races\":[]}]}"));

        read.Should().Throw<ValidationException>().WithMessage("*isSpecialMeeting*");
    }

    [Fact]
    public void ThrowWhenAMeetingIsMissingItsRaces()
    {
        var read = () => new NextDataResultsIndexReader()
            .Read(WrapDocument("{\"data\":[{\"isSpecialMeeting\":false}]}"));

        read.Should().Throw<ValidationException>().WithMessage("*races*");
    }

    [Fact]
    public void ThrowWhenARaceIsMissingItsResultLink()
    {
        var read = () => new NextDataResultsIndexReader()
            .Read(WrapDocument("{\"data\":[{\"isSpecialMeeting\":false,\"races\":[{\"raceUid\":1}]}]}"));

        read.Should().Throw<ValidationException>().WithMessage("*fullResultLink*");
    }

    [Fact]
    public void SkipARaceWhoseResultLinkIsAbsent()
    {
        var links = new NextDataResultsIndexReader().Read(WrapDocument(
            "{\"data\":[{\"isSpecialMeeting\":false,\"races\":[" +
            "{\"fullResultLink\":null},{\"fullResultLink\":\"/results/5/bath/2022-05-11/809925\"}]}]}"));

        links.Should().Equal("/results/5/bath/2022-05-11/809925");
    }

    [Fact]
    public void ThrowWhenThePageHasNoNextDataIsland()
    {
        var read = () => new NextDataResultsIndexReader().Read("<html><body><p>Nothing here.</p></body></html>");

        read.Should().Throw<ValidationException>().WithMessage("*__NEXT_DATA__*");
    }
}
