namespace RacePredictor.Core;

public enum ResultStatus
{
    CompletedRace,
    RaceVoid,
    Fell,
    UnseatedRider,
    SlippedUp,
    RefusedToRace,
    PulledUp,
    BroughtDown,
    Disqualified,
    RanOut,
    Refused
}

public static class ResultStatusExtensions 
{
    public static ResultStatus ToResultStatus(this string s)
    {
        if (int.TryParse(s, out _))
        {
            return ResultStatus.CompletedRace;
        }

        return s switch
        {
            "VOI" => ResultStatus.RaceVoid,
            "F" => ResultStatus.Fell,
            "UR" => ResultStatus.UnseatedRider,
            "SU" => ResultStatus.SlippedUp,
            "RR" => ResultStatus.RefusedToRace,
            "PU" => ResultStatus.PulledUp,
            "BD" => ResultStatus.BroughtDown,
            "DSQ" => ResultStatus.Disqualified,
            "RO" => ResultStatus.RanOut,
            "REF" => ResultStatus.Refused,
            _ => throw new ArgumentOutOfRangeException(nameof(s), $"Unexpected result status '{s}'")
        };
    }
}