namespace RacePredictor.Core;

public enum ResultStatus
{
    CompletedRace,
    RaceVoid,
    Fell,
    UnseatedRider
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
            _ => throw new ArgumentOutOfRangeException(nameof(s), $"Unexpected result status '{s}'")
        };
    }
}