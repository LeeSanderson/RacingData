using System.ComponentModel.DataAnnotations;

namespace RacePredictor.Core.RacingPost;

/// <summary>
/// Cross-validates the JSON-derived runners (the captured data) against the DOM parser's independent
/// reading of the same card (the oracle). Benign edges (e.g. a single non-runner row) are tolerated,
/// but systematic divergence across the runners — or a JSON runner set that does not correspond to
/// the rendered card at all — throws a <see cref="ValidationException"/> and aborts the run, because
/// it means the <c>__NEXT_DATA__</c> node being read no longer matches the page.
///
/// The oracle field set is deliberately limited to fields the DOM parser reads robustly. Age,
/// TopSpeedRating, TrainerName and HeadGear are excluded: the DOM parser is known to be buggy on
/// each (the JSON is authoritative), so comparing them would raise false alarms.
/// </summary>
public static class RaceCardRunnerCrossValidator
{
    private const double OddsTolerance = 0.02;

    public static void Validate(IReadOnlyList<RaceRunner> fromJson, IReadOnlyList<RaceRunner> fromDom)
    {
        if (fromDom.Count == 0)
        {
            // No independent reading to compare against; the JSON reader's own schema validation stands.
            return;
        }

        var jsonByHorseId = fromJson
            .GroupBy(r => r.Horse.Id)
            .ToDictionary(g => g.Key, g => g.First());

        var pairs = new List<(RaceRunner Json, RaceRunner Dom)>();
        var unmatched = 0;
        foreach (var dom in fromDom)
        {
            if (jsonByHorseId.TryGetValue(dom.Horse.Id, out var json))
            {
                pairs.Add((json, dom));
            }
            else
            {
                unmatched++;
            }
        }

        if (unmatched > Tolerance(fromDom.Count))
        {
            throw new ValidationException(
                $"The JSON runner set does not correspond to the rendered race card: {unmatched} of " +
                $"{fromDom.Count} DOM runners have no matching JSON runner by horse id. " +
                "The Racing Post __NEXT_DATA__ structure may have changed.");
        }

        var diverging = OracleFields
            .Select(field => (field.Name, Mismatches: pairs.Count(p => field.Mismatch(p.Json, p.Dom))))
            .Where(f => f.Mismatches > Tolerance(pairs.Count))
            .Select(f => $"{f.Name} ({f.Mismatches}/{pairs.Count})")
            .ToList();

        if (diverging.Count > 0)
        {
            throw new ValidationException(
                "JSON-derived runner data systematically diverges from the DOM oracle on: " +
                string.Join(", ", diverging) + ". " +
                "The Racing Post __NEXT_DATA__ structure may no longer correspond to the rendered card.");
        }
    }

    // A single within-tolerance mismatch (one benign edge) never aborts; divergence across the
    // majority of the runners is treated as structural.
    private static int Tolerance(int count) => Math.Max(1, count / 2);

    private sealed record OracleField(string Name, Func<RaceRunner, RaceRunner, bool> Mismatch);

    private static readonly OracleField[] OracleFields =
    {
        new("HorseName", (j, d) => j.Horse.Name != d.Horse.Name),
        new("JockeyId", (j, d) => j.Jockey.Id != d.Jockey.Id),
        new("JockeyName", (j, d) => j.Jockey.Name != d.Jockey.Name),
        new("TrainerId", (j, d) => j.Trainer.Id != d.Trainer.Id),
        new("RaceCardNumber", (j, d) => j.Attributes.RaceCardNumber != d.Attributes.RaceCardNumber),
        new("StallNumber", (j, d) => j.Attributes.StallNumber != d.Attributes.StallNumber),
        new("Weight", (j, d) => j.Attributes.Weight.TotalPounds != d.Attributes.Weight.TotalPounds),
        new("DaysSinceLastRun", (j, d) => j.Attributes.DaysSinceLastRun != d.Attributes.DaysSinceLastRun),
        new("FormFigures", (j, d) => j.Attributes.FormFigures != d.Attributes.FormFigures),
        new("OfficialRating", (j, d) => j.Statistics.OfficialRating != d.Statistics.OfficialRating),
        new("RacingPostRating", (j, d) => j.Statistics.RacingPostRating != d.Statistics.RacingPostRating),
        new("ForecastOdds", (j, d) => !OddsMatch(j.Statistics.Odds.DecimalOdds, d.Statistics.Odds.DecimalOdds)),
    };

    private static bool OddsMatch(double? a, double? b) =>
        (a is null && b is null) ||
        (a is not null && b is not null && Math.Abs(a.Value - b.Value) <= OddsTolerance);
}
