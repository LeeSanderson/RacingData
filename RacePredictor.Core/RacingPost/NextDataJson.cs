using System.ComponentModel.DataAnnotations;
using System.Text.Json;
using HtmlAgilityPack;

namespace RacePredictor.Core.RacingPost;

internal static class NextDataJson
{
    internal static JsonDocument Parse(HtmlDocument document, string pageDescription)
    {
        var script = document.DocumentNode.SelectSingleNode("//script[@id='__NEXT_DATA__']");
        if (script is null)
        {
            throw new ValidationException(
                $"The {pageDescription} page has no <script id=\"__NEXT_DATA__\"> element. " +
                "The Racing Post page structure may have changed.");
        }

        var json = script.InnerHtml;
        if (string.IsNullOrWhiteSpace(json))
        {
            throw new ValidationException("The __NEXT_DATA__ script element is present but empty.");
        }

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

    internal static JsonElement NavigateTo(JsonElement root, IReadOnlyList<string> path)
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
}
