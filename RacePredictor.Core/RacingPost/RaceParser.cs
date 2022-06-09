using System.Globalization;

namespace RacePredictor.Core.RacingPost
{
    public abstract class RaceParser
    {
        protected string? GetRacePattern(string raceName)
        {
            var pattern = @"((\(|\s)((G|g)rade|(G|g)roup) (\d|[A-Ca-c]|I*)(\)|\s))".FindMatch(raceName);
            if (!string.IsNullOrEmpty(pattern))
                return pattern;

            return raceName.ToLowerInvariant().ContainsAnyIgnoreCase("listed race", "(listed") ? "Listed" : null;
        }

        protected RaceType GetRaceType(string raceName, string? fences)
        {
            if (raceName.ContainsAnyIgnoreCase("national hunt flat"))
                return RaceType.Flat;

            if (!string.IsNullOrEmpty(fences))
            {
                fences = fences.ToLowerInvariant();
                if (fences.Contains("hurdle"))
                    return RaceType.Hurdle;

                if (fences.Contains("chase"))
                    return RaceType.SteepleChase;
            }

        
            if (raceName.ContainsAnyIgnoreCase(" hurdle", "(hurdle)"))
                return RaceType.Hurdle;

            if (raceName.ContainsAnyIgnoreCase(" chase", "(chase)", "steeplechase", "steeple-chase", "steeplchase", "steepl-chase"))
                return RaceType.SteepleChase;

            return raceName.ContainsAnyIgnoreCase(" flat race", "national hunt flat") ? RaceType.Hurdle : RaceType.Other;
        }

        protected RaceSexRestriction GetRaceSexRestriction(string raceName)
        {
            if (raceName.ContainsAnyIgnoreCase("entire colts & fillies", "colts & fillies"))
                return RaceSexRestriction.ColtsAndFillies;

            if (raceName.ContainsAnyIgnoreCase("fillies & mares', 'filles & mares"))
                return RaceSexRestriction.FilliesAndMares;

            if (raceName.ContainsAnyIgnoreCase("fillies"))
                return RaceSexRestriction.Fillies;

            if (raceName.ContainsAnyIgnoreCase("colts & geldings", "colts/geldings", "(c & g)"))
                return RaceSexRestriction.ColdsAndGeldings;

            if (raceName.ContainsAnyIgnoreCase("mares & geldings"))
                return RaceSexRestriction.MaresAndGeldings;

            return raceName.Contains("mares") ? RaceSexRestriction.Mares : RaceSexRestriction.None;
        }

        protected (string, string) GetAgeAndRatingBands(string? bandText)
        {
            var ageBand = string.Empty;
            var ratingBand = string.Empty;
            if (!string.IsNullOrEmpty(bandText))
            {
                var bands = bandText.TrimParens().Split(new[] {",", " "}, StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
                foreach (var band in bands)
                {
                    if (band.Contains("yo"))
                        ageBand = band;
                    else if (band.Contains('-'))
                        ratingBand = band;
                }
            }

            return (ageBand, ratingBand);
        }

        protected DateTime ParseRaceDateAndTime(string raceDate, string raceTime) => 
            DateTime.ParseExact(raceDate + " " + raceTime + " PM", "d MMM yyyy h:mm tt", CultureInfo.InvariantCulture);
    }
}
