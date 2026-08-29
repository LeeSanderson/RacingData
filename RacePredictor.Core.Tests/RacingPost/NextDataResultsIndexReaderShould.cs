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
    public void ExcludeAbandonedRacesThatStillCarryAResultLink()
    {
        var html = ResourceLoader.ReadRacingPostExampleResource("daily_results_20260825_abandoned_races.html");

        var links = new NextDataResultsIndexReader().Read(html);

        links.Count.Should().Be(28);
        links.Where(link => link.Contains("bellewstown")).Should().Equal(
            "/results/176/bellewstown/2026-08-25/927203",
            "/results/176/bellewstown/2026-08-25/927204");
    }

    [Fact]
    public void SkipARaceWhoseFullResultIsNotAvailable()
    {
        var links = new NextDataResultsIndexReader().Read(WrapDocument(
            "{\"data\":[{\"isSpecialMeeting\":false,\"races\":[" +
            "{\"fullResultAvailable\":false,\"fullResultLink\":\"/results/176/bellewstown/2026-08-25/927278\"}," +
            "{\"fullResultAvailable\":true,\"fullResultLink\":\"/results/5/bath/2022-05-11/809925\"}]}]}"));

        links.Should().Equal("/results/5/bath/2022-05-11/809925");
    }

    [Fact]
    public void ThrowWhenARaceIsMissingItsFullResultAvailableFlag()
    {
        var read = () => new NextDataResultsIndexReader().Read(WrapDocument(
            "{\"data\":[{\"isSpecialMeeting\":false,\"races\":[{\"fullResultLink\":\"/results/5/bath/2022-05-11/809925\"}]}]}"));

        read.Should().Throw<ValidationException>().WithMessage("*fullResultAvailable*");
    }

    [Fact]
    public void ThrowWhenTheFullResultAvailableFlagIsNotABoolean()
    {
        var read = () => new NextDataResultsIndexReader().Read(WrapDocument(
            "{\"data\":[{\"isSpecialMeeting\":false,\"races\":[" +
            "{\"fullResultAvailable\":\"yes\",\"fullResultLink\":\"/results/5/bath/2022-05-11/809925\"}]}]}"));

        read.Should().Throw<ValidationException>().WithMessage("*fullResultAvailable*String*");
    }

    [Fact]
    public void ReturnEveryRaceResultLinkForATimeOrderedDayOfRacing()
    {
        var html = ResourceLoader.ReadRacingPostExampleResource("daily_results_timeorder_20260828.html");

        var links = new NextDataResultsIndexReader().Read(html);

        links.Count.Should().Be(50);
        links[0].Should().Be("/results/180/down-royal/2026-08-28/927303");
        links.Should().OnlyHaveUniqueItems();
    }

    [Fact]
    public void ReturnNoLinksForADayWithoutRacing()
    {
        var html = ResourceLoader.ReadRacingPostExampleResource("daily_results_20251225_no_racing.html");

        var links = new NextDataResultsIndexReader().Read(html);

        links.Should().BeEmpty();
    }

    [Fact]
    public void ReturnNoLinksForATimeOrderedDayWithoutRacing()
    {
        var html = ResourceLoader.ReadRacingPostExampleResource("daily_results_timeorder_20251225_no_racing.html");

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
            "{\"fullResultLink\":null}," +
            "{\"fullResultAvailable\":true,\"fullResultLink\":\"/results/5/bath/2022-05-11/809925\"}]}]}"));

        links.Should().Equal("/results/5/bath/2022-05-11/809925");
    }

    [Fact]
    public void ThrowWhenThePageHasNoNextDataIsland()
    {
        var read = () => new NextDataResultsIndexReader().Read("<html><body><p>Nothing here.</p></body></html>");

        read.Should().Throw<ValidationException>().WithMessage("*__NEXT_DATA__*");
    }
}
