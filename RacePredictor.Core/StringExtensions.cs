using System.Text.RegularExpressions;

namespace RacePredictor.Core;

public static class StringExtensions
{
    public static string? FindMatch(this string regexPattern, string? input, int group = 1) =>
        regexPattern.TryExtract(input, group, out var result) ? result : null;

    public static string GetMatch(this string regexPattern, string input, int group = 1) =>
        regexPattern.TryExtract(input, group, out var result)
            ? result!
            : throw new Exception($"Unable to find match for pattern '{regexPattern}' in input '{input}'");

    public static Match GetMatches(this string regexPattern, string input) =>
        regexPattern.TryMatch(input, out var result)
            ? result!
            : throw new Exception($"Unable to find match for pattern '{regexPattern}' in input '{input}'");


    public static bool TryExtract(this string regexPattern, string? input, int group, out string? matched)
    {
        var result = regexPattern.TryMatch(input, out var match);
        matched = result ? match!.Groups[group].Value : null;
        return result;
    }

    public static bool TryMatch(this string regexPattern, string? input, out Match? match)
    {
        var regex = new Regex(regexPattern);
        match = null;
        if (input == null) return false;
        match = regex.Match(input);
        return match.Success;
    }

    public static int? AsOptionalInt(this string? s) => int.TryParse(s, out var result) ? result : null;

    public static int AsInt(this string? s) => int.TryParse(s, out var result)
        ? result
        : throw new Exception($"Unable to convert string '{s}' to integer");


    public static TimeSpan AsTimeSpan(this string? s)
    {
        int minutes, seconds, milliseconds;
        if (@"(\d+)m\s*(\d+)\.(\d+)s".TryMatch(s, out var minuteMatch))
        {
            var groups = minuteMatch!.Groups;
            minutes = groups[1].Value.AsInt();
            seconds = groups[2].Value.AsInt();
            milliseconds = groups[3].Value.AsMilliseconds();
        }
        else if ((@"(\d+)\.(\d+)s").TryMatch(s, out var secondsOnlyMatch))
        {
            var groups = secondsOnlyMatch!.Groups;
            minutes = 0;
            seconds = groups[1].Value.AsInt();
            milliseconds = groups[2].Value.AsMilliseconds();
        }
        else
        {
            throw new Exception($"Unable to convert string '{s}' to TimSpan");

        }

        return new TimeSpan(0, 0, minutes, seconds, milliseconds);
    }

    private static int AsMilliseconds(this string millisecondPart)
    {
        var digits = millisecondPart.Length;
        var factor = digits < 3 ? Math.Pow(10, 3 - digits) : 1;
        return (int)(millisecondPart.AsInt() * factor);
    }

    public static double AsDouble(this string? s) => double.TryParse(s, out var result)
        ? result
        : throw new Exception($"Unable to convert string '{s}' to double");

    public static string TrimAllWhiteSpace(this string? s) => 
        string.IsNullOrEmpty(s) ? string.Empty : Regex.Replace(s, @"(\s|&nbsp;)+", " ").Trim();

    public static string TrimParens(this string? s) =>
        string.IsNullOrEmpty(s) ? string.Empty : s.Trim('(', ')');

    public static string? NullIfEmpty(this string? s) => string.IsNullOrEmpty(s) ? null : s;

    public static bool ContainsAnyIgnoreCase(this string s, params string[] values) =>  values.Any(v => s.Contains(v, StringComparison.CurrentCultureIgnoreCase));
}