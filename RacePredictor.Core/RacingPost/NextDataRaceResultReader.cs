using System.ComponentModel.DataAnnotations;
using System.Text.Json;
using HtmlAgilityPack;

namespace RacePredictor.Core.RacingPost;

/// <summary>
/// Builds a <see cref="RaceResult"/> from the Next.js <c>__NEXT_DATA__</c> JSON island of a race
/// result page. The rendered result table carries no stable hooks (styled-component class names are
/// content-hashed), so the JSON island is the only source. Fail-loud: any structural problem (absent
/// or unparseable island, a moved path, a missing key, or a consumed field of the wrong type) throws
/// a <see cref="ValidationException"/> naming the offending key. A present key carrying a null value
/// is legitimate data and is surfaced as a clean null. A race whose runners are marked "VOI" throws
/// <see cref="VoidRaceException"/>.
/// </summary>
public sealed class NextDataRaceResultReader : RaceParser
{
    private static readonly string[] RaceResultDataPath =
        { "props", "pageProps", "initialState", "raceResult", "data" };

    private static readonly string[] HeaderKeys =
    {
        "raceTime", "raceDate", "courseDisplayName", "raceTitle",
        "raceClass", "agesAllowed", "distanceShort", "going", "obstacles",
    };

    private static readonly string[] DetailsKeys = { "numberOfRunners", "winningTime" };

    private static readonly string[] RunnerKeys =
    {
        "horseUid", "horseName", "saddleClothNo", "drawLabel", "outcomeCode",
        "beatenDistance", "beatenDistanceToWinner", "odds",
        "jockeyName", "jockeyUrl", "trainerName", "trainerUrl",
        "age", "weightStones", "weightPounds", "headgear", "isFirstTimeHeadgear",
        "officialRating", "rpRating", "topspeed",
    };

    private const string VoidOutcomeCode = "VOI";

    public RaceResult Read(string html)
    {
        var document = new HtmlDocument();
        document.LoadHtml(html);
        return Read(document);
    }

    public RaceResult Read(HtmlDocument document)
    {
        using var parsed = NextDataJson.Parse(document, "race result");
        var data = NextDataJson.NavigateTo(parsed.RootElement, RaceResultDataPath);
        var header = RequireObject(data, "header", HeaderKeys);
        var details = RequireObject(data, "details", DetailsKeys);
        var runners = RequireRunners(data);
        EnsureRaceIsNotVoid(runners);

        var course = new RaceEntity(RequireInt(data, "raceResult.data", "courseUid"), Text(header, "courseDisplayName") ?? string.Empty);
        var raceTitle = Text(header, "raceTitle") ?? string.Empty;
        var race = new RaceEntity(RequireInt(data, "raceResult.data", "raceId"), raceTitle);
        var attributes = ReadRaceAttributes(header, details, raceTitle, runners.Count);

        return new RaceResult(course, race, attributes, ReadRunners(runners, course, attributes, details));
    }

    private static RaceAttributes ReadRaceAttributes(JsonElement header, JsonElement details, string raceTitle, int runnerCount)
    {
        var (ageBand, ratingBand) = GetAgeAndRatingBands(Text(header, "agesAllowed"));
        var classification = new RaceClassification(
            GetRaceType(raceTitle, Text(header, "obstacles")),
            ToRaceClass(Text(header, "raceClass")),
            GetRacePattern(raceTitle),
            ratingBand,
            ageBand,
            GetRaceSexRestriction(raceTitle));

        return new RaceAttributes(
            ParseRaceDateAndTime(Text(header, "raceDate") ?? string.Empty, Text(header, "raceTime") ?? string.Empty),
            new RaceDistance(Text(header, "distanceShort") ?? string.Empty),
            classification,
            Text(header, "going"),
            Number(details, "numberOfRunners") ?? runnerCount);
    }

    // The JSON carries the bare class number where the rendered page showed "(Class 4)".
    private static string? ToRaceClass(string? raceClass) =>
        string.IsNullOrEmpty(raceClass) ? null : $"Class {raceClass}";

    private static RaceResultRunner[] ReadRunners(
        IReadOnlyList<JsonElement> runners, RaceEntity course, RaceAttributes attributes, JsonElement details)
    {
        var winningTime = Text(details, "winningTime").AsTimeSpan();
        var lengthsPerSecond = LengthsPerSecondScaleTable.GetLengthsPerSecondScale(
            attributes.Classification.RaceType, attributes.Going, course.Name);

        return runners.Select((runner, index) => ReadRunner(runner, index, winningTime, lengthsPerSecond)).ToArray();
    }

    private static RaceResultRunner ReadRunner(JsonElement runner, int index, TimeSpan winningTime, double lengthsPerSecond)
    {
        var outcomeCode = Text(runner, "outcomeCode") ?? string.Empty;
        var resultStatus = outcomeCode.ToResultStatus();
        var beatenDistance = ToDistance(Text(runner, "beatenDistance"));
        var overallBeatenDistance = Text(runner, "beatenDistanceToWinner") is { } toWinner
            ? ToDistance(toWinner)
            : beatenDistance;

        return new RaceResultRunner(
            new RaceEntity(Number(runner, "horseUid") ?? 0, Text(runner, "horseName") ?? string.Empty),
            ReadPerson(runner, "jockeyUrl", "jockeyName"),
            ReadPerson(runner, "trainerUrl", "trainerName"),
            new RaceRunnerAttributes(
                Number(runner, "saddleClothNo") ?? index + 1,
                Text(runner, "drawLabel").TrimParentheses().AsOptionalInt(),
                Number(runner, "age") ?? 0,
                new RaceWeight(Number(runner, "weightStones") ?? 0, Number(runner, "weightPounds") ?? 0),
                ReadHeadGear(runner)),
            new RaceRunnerStats(
                new RaceOdds(Text(runner, "odds") ?? string.Empty),
                Text(runner, "officialRating").AsOptionalInt(),
                Text(runner, "rpRating").AsOptionalInt(),
                Text(runner, "topspeed").AsOptionalInt()),
            new RaceResultRunnerResults(
                resultStatus,
                resultStatus == ResultStatus.CompletedRace ? outcomeCode.AsInt() : 0,
                beatenDistance,
                overallBeatenDistance,
                winningTime.Add(new TimeSpan((long)(TimeSpan.TicksPerSecond * (overallBeatenDistance / lengthsPerSecond))))));
    }

    // A runner with no profile link (amateur or charity riders, or a jockey the site has yet to fill
    // in) keeps its name and takes id 0 rather than failing the whole race.
    private static RaceEntity ReadPerson(JsonElement runner, string urlKey, string nameKey) =>
        new(@"/(\d+)/".FindMatch(Text(runner, urlKey)).AsOptionalInt() ?? 0, Text(runner, nameKey) ?? string.Empty);

    // First-time headgear rendered as a superscript "1" after the code (e.g. a first-time visor as "v1").
    private static string? ReadHeadGear(JsonElement runner)
    {
        var headGear = Text(runner, "headgear");
        return headGear is null ? null : headGear + (Flag(runner, "isFirstTimeHeadgear") ? "1" : string.Empty);
    }

    private static double ToDistance(string? distance)
    {
        if (string.IsNullOrEmpty(distance))
        {
            return 0;
        }

        return distance
            .Replace("[", "")
            .Replace("]", "")
            .Replace("¼", ".25")
            .Replace("½", ".5")
            .Replace("¾", ".75")
            .Replace("lgnk", "0.4") // Long neck
            .Replace("snk", "0.2") // Short neck
            .Replace("nk", "0.3") // Neck
            .Replace("sht-hd", "0.1") // Short head
            .Replace("shd", "0.1") // Short head (alt)
            .Replace("hd", "0.2") // Head
            .Replace("nse", "0.05") // Nose
            .Replace("dht", "0") // Dead heat
            .Replace("dist", "30") // Distance
            .AsDouble();
    }

    private static void EnsureRaceIsNotVoid(IEnumerable<JsonElement> runners)
    {
        if (runners.Any(runner => Text(runner, "outcomeCode") == VoidOutcomeCode))
        {
            throw new VoidRaceException();
        }
    }

    private static JsonElement RequireObject(JsonElement data, string key, IEnumerable<string> requiredKeys)
    {
        if (data.ValueKind != JsonValueKind.Object ||
            !data.TryGetProperty(key, out var value) ||
            value.ValueKind != JsonValueKind.Object)
        {
            throw new ValidationException(
                $"__NEXT_DATA__ 'raceResult.data' does not contain the expected '{key}' object. " +
                "The Racing Post page structure may have changed.");
        }

        EnsureKeysArePresent(value, requiredKeys, $"raceResult.data.{key}");
        return value;
    }

    private static IReadOnlyList<JsonElement> RequireRunners(JsonElement data)
    {
        if (!data.TryGetProperty("runners", out var runners) || runners.ValueKind != JsonValueKind.Array)
        {
            throw new ValidationException(
                "__NEXT_DATA__ 'raceResult.data' does not contain a 'runners' array. " +
                "The Racing Post page structure may have changed.");
        }

        if (runners.GetArrayLength() == 0)
        {
            throw new ValidationException("__NEXT_DATA__ 'raceResult.data.runners' array is empty.");
        }

        var index = 0;
        var result = new List<JsonElement>();
        foreach (var runner in runners.EnumerateArray())
        {
            if (runner.ValueKind != JsonValueKind.Object)
            {
                throw new ValidationException(
                    $"__NEXT_DATA__ 'raceResult.data.runners[{index}]' is {runner.ValueKind}; expected an object.");
            }

            EnsureKeysArePresent(runner, RunnerKeys, $"raceResult.data.runners[{index}]");
            result.Add(runner);
            index++;
        }

        return result;
    }

    private static void EnsureKeysArePresent(JsonElement element, IEnumerable<string> keys, string path)
    {
        foreach (var key in keys)
        {
            if (!element.TryGetProperty(key, out _))
            {
                throw new ValidationException(
                    $"__NEXT_DATA__ '{path}' is missing the expected key '{key}'. " +
                    "The Racing Post result schema may have changed.");
            }
        }
    }

    private static int RequireInt(JsonElement element, string path, string key)
    {
        if (!element.TryGetProperty(key, out var value))
        {
            throw new ValidationException(
                $"__NEXT_DATA__ '{path}' is missing the expected key '{key}'. " +
                "The Racing Post result schema may have changed.");
        }

        return value.ValueKind switch
        {
            JsonValueKind.Number when value.TryGetInt32(out var number) => number,
            JsonValueKind.String when int.TryParse(value.GetString(), out var parsed) => parsed,
            _ => throw new ValidationException($"__NEXT_DATA__ '{path}.{key}' was {value.ValueKind}; expected an integer."),
        };
    }

    // Sentinel-checked fields: a null token is legitimate absence -> clean null; a number is rendered
    // as its text (ratings and beaten distances arrive as strings but need not be).
    private static string? Text(JsonElement element, string key)
    {
        var value = element.GetProperty(key);
        return value.ValueKind switch
        {
            JsonValueKind.Null => null,
            JsonValueKind.String => value.GetString(),
            JsonValueKind.Number => value.ToString(),
            _ => throw WrongType(key, value.ValueKind, "a string"),
        };
    }

    private static int? Number(JsonElement element, string key)
    {
        var value = element.GetProperty(key);
        return value.ValueKind switch
        {
            JsonValueKind.Null => null,
            JsonValueKind.Number => value.GetInt32(),
            JsonValueKind.String => value.GetString().AsOptionalInt(),
            _ => throw WrongType(key, value.ValueKind, "a number"),
        };
    }

    private static bool Flag(JsonElement element, string key)
    {
        var value = element.GetProperty(key);
        return value.ValueKind switch
        {
            JsonValueKind.True => true,
            JsonValueKind.False => false,
            JsonValueKind.Null => false,
            _ => throw WrongType(key, value.ValueKind, "a boolean"),
        };
    }

    private static ValidationException WrongType(string key, JsonValueKind actual, string expected) =>
        new($"__NEXT_DATA__ result field '{key}' was {actual}; expected {expected}.");
}
