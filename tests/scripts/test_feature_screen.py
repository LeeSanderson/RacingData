"""Tests for feature_screen pure utility functions."""

from race_analytics.scripts.feature_screen import (
    check_no_odds_features,
    rank_features,
    select_features,
)


def test_rank_features_returns_highest_first():
    """rank_features sorts by importance descending."""
    importances = {"feat_a": 0.2, "feat_b": 0.8, "feat_c": 0.5}
    result = rank_features(importances)
    names = [name for name, _ in result]
    assert names == ["feat_b", "feat_c", "feat_a"]


def test_select_features_keeps_above_threshold():
    """select_features drops features below min_importance."""
    importances = {"feat_a": 0.5, "feat_b": 0.0, "feat_c": 2e-7}
    selected = select_features(importances, min_importance=1e-6)
    assert selected == {"feat_a"}


def test_select_features_default_threshold_drops_exactly_zero():
    """select_features with default threshold drops zero-importance features."""
    importances = {"feat_a": 0.1, "feat_b": 0.0}
    assert "feat_b" not in select_features(importances)


def test_check_no_odds_features_clean():
    """check_no_odds_features returns True when no odds-related names present."""
    features = ["DistanceInMeters", "WeightInPounds", "RaceClass", "Age"]
    assert check_no_odds_features(features) is True


def test_check_no_odds_features_detects_odds_keyword():
    """check_no_odds_features returns False when an odds keyword appears."""
    features = ["DistanceInMeters", "DecimalOdds"]
    assert check_no_odds_features(features) is False
