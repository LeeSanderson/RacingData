using System.ComponentModel.DataAnnotations;
using System.Text;
using System.Text.Json;
using HtmlAgilityPack;

namespace RacePredictor.Core.RacingPost;

/// <summary>
/// Locates the Next.js <c>__NEXT_DATA__</c> JSON island in a race-card page, navigates to the
/// per-runner array and race object, and returns a validated <see cref="NextDataRaceCardView"/>.
/// Fail-loud: any structural problem (absent/unparseable island, a moved runners path, a missing
/// sentinel key, or a consumed field of the wrong type) throws a <see cref="ValidationException"/>
/// naming the offending key/path/type. A present key carrying a null value is legitimate data and
/// is surfaced as a clean null without throwing.
/// </summary>
public sealed class NextDataRaceCardReader
{
    private static readonly string[] RacePageDataPath =
        { "props", "pageProps", "initialState", "racePage", "data" };

    // Every key consumed by this slice must exist on each runner. A missing key is a structural
    // change and throws; a present key with a null value stays a clean null.
    private static readonly string[] SentinelKeys =
    {
        "horseId", "horseName", "countryOrigin",
        "jockeyId", "jockeyName", "trainerId", "trainerName",
        "ownerId", "ownerName",
        "sireName", "sireCountry", "damName",
        "age", "startNumber", "draw",
        "formattedWeightStones", "formattedWeightPounds",
        "daysSinceLastRun", "formFiguresData",
        "officialRatingToday", "rpPostmark", "rpTopspeed",
        "horseHeadGear", "forecastOddsValue", "nonRunner", "irishReserve",
        "horseHeadGearFirstTime", "geldingFirstTime", "windSurgery", "trainerRtf",
        "weightAllowanceLbs", "jockeyFirstTime", "newTrainerRacesCount", "spotlight",
    };

    public NextDataRaceCardView Read(string html)
    {
        var document = new HtmlDocument();
        document.LoadHtml(html);
        return Read(document);
    }

    public NextDataRaceCardView Read(HtmlDocument document)
    {
        var json = ExtractNextDataJson(document);
        using var parsed = ParseJson(json);
        var data = NavigateTo(parsed.RootElement, RacePageDataPath);
        var (courseId, raceId, countryCode) = ReadRaceLevel(data);
        var forecastOdds = ReadForecastOdds(data);
        var runners = ReadRunners(data, countryCode, forecastOdds);
        return new NextDataRaceCardView(courseId, raceId, countryCode, runners);
    }

    private static string ExtractNextDataJson(HtmlDocument document)
    {
        var script = document.DocumentNode.SelectSingleNode("//script[@id='__NEXT_DATA__']");
        if (script is null)
        {
            throw new ValidationException(
                "The race-card page has no <script id=\"__NEXT_DATA__\"> element. " +
                "The Racing Post page structure may have changed.");
        }

        var json = script.InnerHtml;
        if (string.IsNullOrWhiteSpace(json))
        {
            throw new ValidationException("The __NEXT_DATA__ script element is present but empty.");
        }

        return json;
    }

    private static JsonDocument ParseJson(string json)
    {
        try
        {
            return JsonDocument.Parse(json);
        }
        catch (JsonException ex)
        {
            throw new ValidationException(
                $"The __NEXT_DATA__ script content could not be parsed as JSON: {ex.Message}");
        }
    }

    private static JsonElement NavigateTo(JsonElement root, IReadOnlyList<string> path)
    {
        var current = root;
        var traversed = "$";
        foreach (var segment in path)
        {
            if (current.ValueKind != JsonValueKind.Object || !current.TryGetProperty(segment, out var next))
            {
                throw new ValidationException(
                    $"__NEXT_DATA__ JSON does not contain the expected path '{traversed}.{segment}'. " +
                    "The Racing Post page structure may have changed.");
            }

            current = next;
            traversed = $"{traversed}.{segment}";
        }

        return current;
    }

    private static (int courseId, int raceId, string countryCode) ReadRaceLevel(JsonElement data)
    {
        if (data.ValueKind != JsonValueKind.Object || !data.TryGetProperty("race", out var race) || race.ValueKind != JsonValueKind.Object)
        {
            throw new ValidationException(
                "__NEXT_DATA__ JSON does not contain the expected 'racePage.data.race' object. " +
                "The Racing Post page structure may have changed.");
        }

        return (RequireIntFromNumberOrString(race, "courseId"),
            RequireIntFromNumberOrString(race, "raceId"),
            RequireString(race, "countryCode"));
    }

    private static IReadOnlyList<NextDataRunner> ReadRunners(JsonElement data, string raceCountryCode, IReadOnlyDictionary<int, string> forecastOdds)
    {
        if (!data.TryGetProperty("runners", out var runners) || runners.ValueKind != JsonValueKind.Array)
        {
            throw new ValidationException(
                "__NEXT_DATA__ JSON does not contain a 'racePage.data.runners' array. " +
                "The Racing Post page structure may have changed.");
        }

        if (runners.GetArrayLength() == 0)
        {
            throw new ValidationException("__NEXT_DATA__ 'racePage.data.runners' array is empty.");
        }

        var result = new List<NextDataRunner>();
        var index = 0;
        foreach (var runner in runners.EnumerateArray())
        {
            ValidateSentinelKeys(runner, index);
            result.Add(BuildRunner(runner, index, raceCountryCode, forecastOdds));
            index++;
        }

        return result;
    }

    // The betting forecast lives in a race-level array (the JSON analog of the rendered forecast the
    // DOM parser scrapes), each entry fanning one price out to one or more horses. A missing forecast
    // is legitimate absence (the card has none) -> an empty map, every runner left at SP -> never throws.
    private static IReadOnlyDictionary<int, string> ReadForecastOdds(JsonElement data)
    {
        var map = new Dictionary<int, string>();
        if (!data.TryGetProperty("raceDetails", out var raceDetails) ||
            raceDetails.ValueKind != JsonValueKind.Object ||
            !raceDetails.TryGetProperty("bettingForecast", out var forecast) ||
            forecast.ValueKind != JsonValueKind.Array)
        {
            return map;
        }

        foreach (var entry in forecast.EnumerateArray())
        {
            if (entry.ValueKind != JsonValueKind.Object ||
                !entry.TryGetProperty("oddsDesc", out var oddsDesc) || oddsDesc.ValueKind != JsonValueKind.String ||
                !entry.TryGetProperty("horses", out var horses) || horses.ValueKind != JsonValueKind.Array)
            {
                continue;
            }

            var desc = oddsDesc.GetString();
            if (string.IsNullOrEmpty(desc))
            {
                continue;
            }

            foreach (var horse in horses.EnumerateArray())
            {
                if (horse.ValueKind == JsonValueKind.Object &&
                    horse.TryGetProperty("horseId", out var horseId) &&
                    horseId.ValueKind == JsonValueKind.Number &&
                    horseId.TryGetInt32(out var id))
                {
                    map[id] = desc;
                }
            }
        }

        return map;
    }

    private static void ValidateSentinelKeys(JsonElement runner, int index)
    {
        if (runner.ValueKind != JsonValueKind.Object)
        {
            throw new ValidationException(
                $"__NEXT_DATA__ runner[{index}] is {runner.ValueKind}; expected an object.");
        }

        foreach (var key in SentinelKeys)
        {
            if (!runner.TryGetProperty(key, out _))
            {
                throw new ValidationException(
                    $"__NEXT_DATA__ runner[{index}] is missing the expected key '{key}'. " +
                    "The Racing Post runner schema may have changed.");
            }
        }
    }

    private static NextDataRunner BuildRunner(JsonElement runner, int index, string raceCountryCode, IReadOnlyDictionary<int, string> forecastOdds)
    {
        var fields = new RunnerFields(runner, index);

        var horseId = fields.NumberOrNull("horseId");
        var rawName = fields.StringOrNull("horseName");
        var country = fields.StringOrNull("countryOrigin");

        // forecastOddsValue is the fractional ratio (e.g. "11/2" -> 5.5); decimal odds are ratio + 1,
        // matching the RaceOdds the DOM parser derives from the same forecast.
        var forecastRatio = fields.NumberAsDoubleOrNull("forecastOddsValue");

        // The fractional price string ("11/2") comes from the race-level betting forecast, keyed by
        // horse id; absent there leaves the runner at SP.
        var forecastFractional = horseId.HasValue && forecastOdds.TryGetValue(horseId.Value, out var desc) ? desc : null;

        // A claiming jockey's allowance is both folded into the rendered jockey name (for DOM fidelity)
        // and captured in its own column, so it is read once here.
        var jockeyAllowanceLbs = fields.NumberOrNull("weightAllowanceLbs");

        return new NextDataRunner(
            horseId,
            ReconstructHorseName(rawName, country, raceCountryCode),
            fields.NumberOrNull("jockeyId"),
            ReconstructJockeyName(fields.StringOrNull("jockeyName"), jockeyAllowanceLbs),
            fields.NumberOrNull("trainerId"),
            fields.StringOrNull("trainerName"),
            fields.NumberOrNull("ownerId"),
            fields.StringOrNull("ownerName"),
            fields.StringOrNull("sireName"),
            fields.StringOrNull("sireCountry"),
            fields.StringOrNull("damName"),
            fields.NumberOrNull("age") ?? 0,
            new RaceWeight(fields.NumberOrNull("formattedWeightStones") ?? 0, fields.NumberOrNull("formattedWeightPounds") ?? 0),
            fields.NumberOrNull("startNumber") ?? 0,
            fields.NumberOrNull("draw"),
            fields.IntFromStringOrNull("daysSinceLastRun"),
            fields.FormFigures("formFiguresData"),
            fields.RatingOrNull("officialRatingToday"),
            fields.RatingOrNull("rpPostmark"),
            fields.RatingOrNull("rpTopspeed"),
            fields.StringOrNull("horseHeadGear"),
            forecastFractional,
            forecastRatio.HasValue ? forecastRatio.Value + 1.0 : null,
            fields.Bool("nonRunner") || fields.Bool("irishReserve"),
            fields.BoolOrNull("horseHeadGearFirstTime"),
            fields.BoolOrNull("geldingFirstTime"),
            fields.NumberOrNull("windSurgery"),
            fields.NumberOrNull("trainerRtf"),
            jockeyAllowanceLbs,
            fields.BoolOrNull("jockeyFirstTime"),
            fields.NumberOrNull("newTrainerRacesCount"),
            country,
            fields.StringOrNull("spotlight"));
    }

    // Racing Post appends a horse's country of origin to its name only when that country differs
    // from the country the race is run in (e.g. "Relocal FR" at a GB meeting, "Big Cypress GB" at
    // an IRE meeting). This reproduces the name the DOM parser reads from the rendered anchor.
    private static string? ReconstructHorseName(string? name, string? country, string raceCountryCode) =>
        string.IsNullOrEmpty(name) || string.IsNullOrEmpty(country) || country == raceCountryCode
            ? name
            : $"{name} {country}";

    // A claiming jockey's weight allowance is rendered after the name as "(N)" (e.g. "Fern O'Brien
    // (5)"); the DOM parser reads it as part of the name, so the reader reproduces it.
    private static string? ReconstructJockeyName(string? name, int? allowanceLbs) =>
        string.IsNullOrEmpty(name) || allowanceLbs is not > 0
            ? name
            : $"{name} ({allowanceLbs})";

    private static int RequireIntFromNumberOrString(JsonElement parent, string key)
    {
        var value = RequireRaceField(parent, key);
        switch (value.ValueKind)
        {
            case JsonValueKind.Number when value.TryGetInt32(out var number):
                return number;
            case JsonValueKind.String when int.TryParse(value.GetString(), out var parsed):
                return parsed;
            default:
                throw new ValidationException(
                    $"__NEXT_DATA__ race field '{key}' was {value.ValueKind}; expected an integer.");
        }
    }

    private static string RequireString(JsonElement parent, string key)
    {
        var value = RequireRaceField(parent, key);
        return value.ValueKind == JsonValueKind.String
            ? value.GetString()!
            : throw new ValidationException(
                $"__NEXT_DATA__ race field '{key}' was {value.ValueKind}; expected a string.");
    }

    private static JsonElement RequireRaceField(JsonElement race, string key) =>
        race.TryGetProperty(key, out var value)
            ? value
            : throw new ValidationException(
                $"__NEXT_DATA__ 'racePage.data.race' is missing the expected key '{key}'. " +
                "The Racing Post page structure may have changed.");

    // Typed accessors over one runner object. Each assumes the key is present (sentinel-checked).
    // A null token is legitimate absence -> clean null; a present non-null value of the wrong JSON
    // kind is a structural change -> throw.
    private readonly struct RunnerFields(JsonElement runner, int index)
    {
        public int? NumberOrNull(string key)
        {
            var value = runner.GetProperty(key);
            return value.ValueKind switch
            {
                JsonValueKind.Null => null,
                JsonValueKind.Number => value.GetInt32(),
                _ => throw WrongType(key, value.ValueKind, "a number"),
            };
        }

        public double? NumberAsDoubleOrNull(string key)
        {
            var value = runner.GetProperty(key);
            return value.ValueKind switch
            {
                JsonValueKind.Null => null,
                JsonValueKind.Number => value.GetDouble(),
                _ => throw WrongType(key, value.ValueKind, "a number"),
            };
        }

        public string? StringOrNull(string key)
        {
            var value = runner.GetProperty(key);
            return value.ValueKind switch
            {
                JsonValueKind.Null => null,
                JsonValueKind.String => value.GetString(),
                _ => throw WrongType(key, value.ValueKind, "a string"),
            };
        }

        public bool Bool(string key)
        {
            var value = runner.GetProperty(key);
            return value.ValueKind switch
            {
                JsonValueKind.True => true,
                JsonValueKind.False => false,
                JsonValueKind.Null => false,
                _ => throw WrongType(key, value.ValueKind, "a boolean"),
            };
        }

        // Like Bool but null-preserving: a present-but-null flag stays a clean null (absent from the
        // card) rather than collapsing to false, so "flag absent" and "flag not set" stay distinct.
        public bool? BoolOrNull(string key)
        {
            var value = runner.GetProperty(key);
            return value.ValueKind switch
            {
                JsonValueKind.True => true,
                JsonValueKind.False => false,
                JsonValueKind.Null => null,
                _ => throw WrongType(key, value.ValueKind, "a boolean"),
            };
        }

        // Ratings render as an integer or the string "-" (unrated). The dash and null both mean
        // "no rating"; any other non-numeric value is treated as absent rather than fatal.
        public int? RatingOrNull(string key)
        {
            var value = runner.GetProperty(key);
            return value.ValueKind switch
            {
                JsonValueKind.Number => value.GetInt32(),
                JsonValueKind.String => null,
                JsonValueKind.Null => null,
                _ => throw WrongType(key, value.ValueKind, "a number or \"-\""),
            };
        }

        // Days-since-last-run is carried as a string ("21"); debut runners carry null.
        public int? IntFromStringOrNull(string key)
        {
            var value = runner.GetProperty(key);
            return value.ValueKind switch
            {
                JsonValueKind.Null => null,
                JsonValueKind.Number => value.GetInt32(),
                JsonValueKind.String => int.TryParse(value.GetString(), out var parsed) ? parsed : null,
                _ => throw WrongType(key, value.ValueKind, "a number or string"),
            };
        }

        // Form figures arrive as an ordered array of { figure, isBold, position } objects; the DOM
        // parser reads the same figures concatenated (e.g. "3-1958").
        public string? FormFigures(string key)
        {
            var value = runner.GetProperty(key);
            if (value.ValueKind == JsonValueKind.Null)
            {
                return null;
            }

            if (value.ValueKind != JsonValueKind.Array)
            {
                throw WrongType(key, value.ValueKind, "an array");
            }

            var builder = new StringBuilder();
            foreach (var entry in value.EnumerateArray())
            {
                if (entry.ValueKind == JsonValueKind.Object &&
                    entry.TryGetProperty("figure", out var figure) &&
                    figure.ValueKind == JsonValueKind.String)
                {
                    builder.Append(figure.GetString());
                }
            }

            return builder.Length == 0 ? null : builder.ToString();
        }

        private ValidationException WrongType(string key, JsonValueKind actual, string expected) =>
            new($"__NEXT_DATA__ runner[{index}] field '{key}' was {actual}; expected {expected}.");
    }
}
