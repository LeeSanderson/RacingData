import pandas as pd
import pytest

from race_analytics.algorithms.race_rules_gate import RaceRulesGate


def _race(race_id: int, distance_m: float | None = 1600.0, cls: str | None = None) -> dict:
    row = {"RaceId": race_id, "HorseId": race_id * 10}
    if distance_m is not None:
        row["DistanceInMeters"] = distance_m
    if cls is not None:
        row["Class"] = cls
    return row


# ── Sprint rule ───────────────────────────────────────────────────────────────

def test_sprint_race_is_excluded():
    gate = RaceRulesGate()
    races = pd.DataFrame([_race(1, distance_m=1000.0)])  # ~5f
    assert 1 in gate.excluded_race_ids(races)


def test_non_sprint_race_is_kept():
    gate = RaceRulesGate()
    races = pd.DataFrame([_race(1, distance_m=1609.0)])  # ~8f
    assert 1 not in gate.excluded_race_ids(races)


def test_exactly_6f_is_kept():
    gate = RaceRulesGate()
    races = pd.DataFrame([_race(1, distance_m=6 * 201.168)])
    assert 1 not in gate.excluded_race_ids(races)


def test_missing_distance_is_not_excluded():
    gate = RaceRulesGate()
    races = pd.DataFrame([{"RaceId": 1, "HorseId": 10}])
    assert 1 not in gate.excluded_race_ids(races)


# ── Class 6 rule ──────────────────────────────────────────────────────────────

def test_class6_race_is_excluded():
    gate = RaceRulesGate()
    races = pd.DataFrame([_race(1, cls="Class 6")])
    assert 1 in gate.excluded_race_ids(races)


def test_class5_race_is_kept():
    gate = RaceRulesGate()
    races = pd.DataFrame([_race(1, cls="Class 5")])
    assert 1 not in gate.excluded_race_ids(races)


def test_missing_class_is_not_excluded():
    gate = RaceRulesGate()
    races = pd.DataFrame([{"RaceId": 1, "HorseId": 10, "DistanceInMeters": 1600.0}])
    assert 1 not in gate.excluded_race_ids(races)


def test_class6_with_whitespace_is_excluded():
    gate = RaceRulesGate()
    races = pd.DataFrame([_race(1, cls="  Class 6  ")])
    assert 1 in gate.excluded_race_ids(races)


def test_nan_class_is_not_excluded():
    gate = RaceRulesGate()
    races = pd.DataFrame([_race(1)])
    races["Class"] = float("nan")
    assert 1 not in gate.excluded_race_ids(races)


# ── Combined ──────────────────────────────────────────────────────────────────

def test_sprint_and_class6_race_is_excluded():
    gate = RaceRulesGate()
    races = pd.DataFrame([_race(1, distance_m=1000.0, cls="Class 6")])
    assert 1 in gate.excluded_race_ids(races)


def test_non_sprint_non_class6_is_kept():
    gate = RaceRulesGate()
    races = pd.DataFrame([_race(1, distance_m=1800.0, cls="Class 5")])
    assert 1 not in gate.excluded_race_ids(races)


def test_empty_dataframe_returns_empty_set():
    gate = RaceRulesGate()
    assert gate.excluded_race_ids(pd.DataFrame()) == set()


# ── Multi-horse race (dedup) ──────────────────────────────────────────────────

def test_multi_horse_sprint_race_excluded_once():
    gate = RaceRulesGate()
    races = pd.DataFrame([
        {"RaceId": 1, "HorseId": 10, "DistanceInMeters": 900.0},
        {"RaceId": 1, "HorseId": 11, "DistanceInMeters": 900.0},
    ])
    excluded = gate.excluded_race_ids(races)
    assert excluded == {1}
