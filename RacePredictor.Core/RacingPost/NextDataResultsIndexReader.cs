using System.ComponentModel.DataAnnotations;
using System.Text.Json;
using HtmlAgilityPack;

namespace RacePredictor.Core.RacingPost;

/// <summary>
/// Reads the per-race result links for one day from the Next.js <c>__NEXT_DATA__</c> JSON island of a
/// daily results index page. The rendered page only lists races once a meeting accordion is expanded,
/// so the JSON island is the only complete source. Fail-loud: any structural problem (absent or
/// unparseable island, a moved path, a missing key, or a consumed field of the wrong type) throws a
/// <see cref="ValidationException"/>. A day with no racing is recognised by the page's own
/// "no results" message and yields an empty list.
/// </summary>
public sealed class NextDataResultsIndexReader
{
    private static readonly string[] ResultsPath = { "props", "pageProps", "initialState", "results" };

    private const string NoResultsMessageXPath = "//*[@data-testid='Text__NoResultsMessage']";

    public IReadOnlyList<string> Read(string html)
    {
        var document = new HtmlDocument();
        document.LoadHtml(html);
        return Read(document);
    }

    public IReadOnlyList<string> Read(HtmlDocument document)
    {
        using var parsed = NextDataJson.Parse(document, "daily results");
        var results = NextDataJson.NavigateTo(parsed.RootElement, ResultsPath);
        if (results.ValueKind != JsonValueKind.Object || !results.TryGetProperty("data", out var meetings))
        {
            throw new ValidationException(
                "__NEXT_DATA__ JSON does not contain the expected 'results.data' key. " +
                "The Racing Post page structure may have changed.");
        }

        switch (meetings.ValueKind)
        {
            case JsonValueKind.Null:
                EnsureNoRacingMessageIsPresent(document);
                return [];
            case JsonValueKind.Array:
                return ReadResultLinks(meetings);
            default:
                throw new ValidationException(
                    $"__NEXT_DATA__ 'results.data' was {meetings.ValueKind}; expected an array or null.");
        }
    }

    private static void EnsureNoRacingMessageIsPresent(HtmlDocument document)
    {
        if (document.DocumentNode.SelectSingleNode(NoResultsMessageXPath) is null)
        {
            throw new ValidationException(
                "__NEXT_DATA__ 'results.data' was null but the page carries no 'no results for this date' " +
                "message, so the absent results cannot be read as a day without racing. " +
                "The Racing Post page structure may have changed.");
        }
    }

    private static IReadOnlyList<string> ReadResultLinks(JsonElement meetings)
    {
        var links = new List<string>();
        var index = 0;
        foreach (var meeting in meetings.EnumerateArray())
        {
            if (meeting.ValueKind != JsonValueKind.Object)
            {
                throw new ValidationException(
                    $"__NEXT_DATA__ 'results.data[{index}]' is {meeting.ValueKind}; expected an object.");
            }

            // Special meetings ("Worldwide Stakes", "World Pool Races", "Scoop6") are highlight
            // groupings that repeat races already listed under their own course, so skipping them
            // keeps each race in the day exactly once.
            if (!IsSpecialMeeting(meeting, index))
            {
                links.AddRange(ReadMeetingResultLinks(meeting, index));
            }

            index++;
        }

        return links;
    }

    private static bool IsSpecialMeeting(JsonElement meeting, int index)
    {
        if (!meeting.TryGetProperty("isSpecialMeeting", out var isSpecial))
        {
            throw new ValidationException(
                $"__NEXT_DATA__ 'results.data[{index}]' is missing the expected key 'isSpecialMeeting'. " +
                "The Racing Post results schema may have changed.");
        }

        return isSpecial.ValueKind switch
        {
            JsonValueKind.True => true,
            JsonValueKind.False => false,
            JsonValueKind.Null => false,
            _ => throw new ValidationException(
                $"__NEXT_DATA__ 'results.data[{index}].isSpecialMeeting' was {isSpecial.ValueKind}; expected a boolean."),
        };
    }

    private static List<string> ReadMeetingResultLinks(JsonElement meeting, int meetingIndex)
    {
        if (!meeting.TryGetProperty("races", out var races))
        {
            throw new ValidationException(
                $"__NEXT_DATA__ 'results.data[{meetingIndex}]' is missing the expected key 'races'. " +
                "The Racing Post results schema may have changed.");
        }

        var links = new List<string>();
        if (races.ValueKind == JsonValueKind.Null)
        {
            return links;
        }

        if (races.ValueKind != JsonValueKind.Array)
        {
            throw new ValidationException(
                $"__NEXT_DATA__ 'results.data[{meetingIndex}].races' was {races.ValueKind}; expected an array or null.");
        }

        var raceIndex = 0;
        foreach (var race in races.EnumerateArray())
        {
            if (ReadResultLink(race, meetingIndex, raceIndex) is { } link)
            {
                links.Add(link);
            }

            raceIndex++;
        }

        return links;
    }

    // A null link is legitimate absence (an abandoned or void race has no result page to download).
    private static string? ReadResultLink(JsonElement race, int meetingIndex, int raceIndex)
    {
        var path = $"results.data[{meetingIndex}].races[{raceIndex}]";
        if (race.ValueKind != JsonValueKind.Object)
        {
            throw new ValidationException($"__NEXT_DATA__ '{path}' is {race.ValueKind}; expected an object.");
        }

        if (!race.TryGetProperty("fullResultLink", out var link))
        {
            throw new ValidationException(
                $"__NEXT_DATA__ '{path}' is missing the expected key 'fullResultLink'. " +
                "The Racing Post results schema may have changed.");
        }

        return link.ValueKind switch
        {
            JsonValueKind.Null => null,
            JsonValueKind.String => link.GetString().NullIfEmpty(),
            _ => throw new ValidationException(
                $"__NEXT_DATA__ '{path}.fullResultLink' was {link.ValueKind}; expected a string."),
        };
    }
}
