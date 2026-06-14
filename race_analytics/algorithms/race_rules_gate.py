import pandas as pd

_FURLONG_M = 201.168
_SPRINT_THRESHOLD_FURLONGS = 6.0


class RaceRulesGate:
    """Hard race-shape exclusions (Filter B).

    Rule A: exclude sprint races (distance < 6 furlongs).
    Rule B: exclude Class 6 races.
    Missing attribute -> race is not excluded by that rule.
    """

    def excluded_race_ids(self, races: pd.DataFrame) -> set[str]:
        if races.empty or "RaceId" not in races.columns:
            return set()
        race_level = races.drop_duplicates("RaceId")
        excl = pd.Series(False, index=race_level.index)

        if "DistanceInMeters" in race_level.columns:
            dm = pd.to_numeric(race_level["DistanceInMeters"], errors="coerce")
            excl |= dm.notna() & (dm / _FURLONG_M < _SPRINT_THRESHOLD_FURLONGS)  # pyright: ignore[reportAttributeAccessIssue, reportOperatorIssue]  # to_numeric returns a Series

        if "Class" in race_level.columns:
            excl |= race_level["Class"].fillna("").str.strip() == "Class 6"

        return set(race_level.loc[excl, "RaceId"])
