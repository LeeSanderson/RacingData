from dataclasses import dataclass
from datetime import datetime
from typing import Self

@dataclass
class Race:
    RaceId: int
    RaceName: str
    CourseId: int
    CourseName: str
    Off: datetime

def dt(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%m/%d/%Y %H:%M:%S")

Ballinrobe20thAt1515 = Race(
    789601,
    "Stores Maiden Hurdle",
    175,
    "Ballinrobe (IRE)",
    dt("07/20/2021 15:15:00"))

Chelmsford21stAt1805 = Race(
    788291,
    "Your First Bet Apprentice Handicap",
    1083,
    "Chelmsford (AW)",
    dt("07/21/2021 18:05:00"))

Nottingham22ndAt1815 = Race(
    787996,
    "National Race Horse Week Handicap",
    40,
    "Nottingham",
    dt("07/22/2021 18:15:00"))

Wolverhampton24thAt1300 = Race(
    788296,
    "Download The Free At The Races App Handicap (Div I)",
    513,
    "Wolverhampton (AW)",
    dt("07/24/2021 13:00:00"))


@dataclass
class Horse:
    HorseId: int
    HorseName: str

DuckAndVanish = Horse(2851323, "Duck And Vanish")
LaylaDaffodil = Horse(3239220, "Layla's Daffodil")
SecretSecret = Horse(2643487, "Secret Secret")
ComeSeptember = Horse(2685600, "Come September")
SelfAssessed = Horse(2886443, "Self Assessed")

@dataclass
class Jockey:
    JockeyId: int
    JockeyName: str

PhilipDonovan = Jockey(92157, "Philip Donovan")
ShaneFitzgerald = Jockey(100972, "Shane Fitzgerald")
PaulTown = Jockey(100971, "Paul Town")
SimonTorrens = Jockey(93137, "Simon Torrens")
KevinSexton = Jockey(90704, "Kevin Sexton")

@dataclass
class RaceResult:
    RaceId: int
    RaceName: str
    CourseId: int
    CourseName: str
    Off: datetime
    HorseId: int
    HorseName: str
    JockeyId: int
    JockeyName: str
    Going: str

    @staticmethod
    def new(race: Race, horse: Horse, jockey: Jockey, Going: str = "Good") -> "RaceResult":
        return RaceResult(
            race.RaceId,
            race.RaceName,
            race.CourseId,
            race.CourseName,
            race.Off,
            horse.HorseId,
            horse.HorseName,
            jockey.JockeyId,
            jockey.JockeyName,
            Going
        )
