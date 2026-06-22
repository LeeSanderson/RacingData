namespace RacePredictor.Core;

public class RaceRunner
{
    public RaceRunner(
        RaceEntity horse,
        RaceEntity jockey,
        RaceEntity trainer,
        RaceRunnerAttributes attributes,
        RaceRunnerStats statistics,
        RaceEntity? owner = null,
        RaceRunnerBreeding? breeding = null,
        RaceRunnerExtras? extras = null)
    {
        Horse = horse;
        Jockey = jockey;
        Trainer = trainer;
        Attributes = attributes;
        Statistics = statistics;
        Owner = owner;
        Breeding = breeding;
        Extras = extras;
    }

    public RaceEntity Horse { get; }
    public RaceEntity Jockey { get; }
    public RaceEntity Trainer { get; }

    // Owner is a forward-only racecard fact (the JSON island is the sole capture source); it is null
    // on the DOM-oracle reading and excluded from cross-validation. Optional so the DOM parser and the
    // results layout are unaffected.
    public RaceEntity? Owner { get; }

    // Breeding (sire/dam) is a forward-only racecard fact like Owner: null on the DOM-oracle reading
    // and excluded from cross-validation. Trailing optional so the DOM parser and results layout are
    // unaffected.
    public RaceRunnerBreeding? Breeding { get; }

    // Per-runner extras (first-time flags, trainerRtf, jockey allowance, new-trainer count, country,
    // Spotlight prose) — like Owner/Breeding a forward-only JSON-only fact, null on the DOM-oracle
    // reading and excluded from cross-validation. Trailing optional so the DOM parser and results
    // layout are unaffected.
    public RaceRunnerExtras? Extras { get; }

    public RaceRunnerAttributes Attributes { get; }
    public RaceRunnerStats Statistics { get; }
}