import pandas as pd
import numpy as np
import pytest
from race_analytics.algorithms.confidence_gate import ConfidenceGate


# ── score() ──────────────────────────────────────────────────────────────────

class TestScore:
    def test_top_prob_returns_highest(self):
        gate = ConfidenceGate("top_prob")
        assert gate.score(pd.Series([0.6, 0.3, 0.1])) == pytest.approx(0.6)

    def test_gap_returns_top_minus_second(self):
        gate = ConfidenceGate("gap")
        assert gate.score(pd.Series([0.6, 0.3, 0.1])) == pytest.approx(0.3)

    def test_single_horse_top_prob(self):
        gate = ConfidenceGate("top_prob")
        assert gate.score(pd.Series([0.8])) == pytest.approx(0.8)

    def test_single_horse_gap_equals_top_prob(self):
        # no second horse → gap = top - 0 = top
        gate = ConfidenceGate("gap")
        assert gate.score(pd.Series([0.8])) == pytest.approx(0.8)

    def test_empty_race_top_prob_returns_zero(self):
        gate = ConfidenceGate("top_prob")
        assert gate.score(pd.Series([], dtype=float)) == pytest.approx(0.0)

    def test_empty_race_gap_returns_zero(self):
        gate = ConfidenceGate("gap")
        assert gate.score(pd.Series([], dtype=float)) == pytest.approx(0.0)

    def test_invalid_metric_raises(self):
        with pytest.raises(ValueError, match="metric must be"):
            ConfidenceGate("invalid")


# ── calibrate() / keep() ─────────────────────────────────────────────────────

class TestCalibrate:
    def test_full_coverage_threshold_at_minimum_score(self):
        gate = ConfidenceGate("top_prob")
        gate.calibrate([0.3, 0.5, 0.7, 0.9], coverage=1.0)
        # threshold = quantile(scores, 0.0) = 0.3
        assert gate.keep(0.3)
        assert gate.keep(0.9)

    def test_half_coverage_keeps_top_half(self):
        gate = ConfidenceGate("top_prob")
        gate.calibrate([0.2, 0.4, 0.6, 0.8], coverage=0.5)
        # threshold = quantile(0.5) = median([0.2,0.4,0.6,0.8]) = 0.5
        assert gate.keep(0.6)
        assert gate.keep(0.8)
        assert not gate.keep(0.4)
        assert not gate.keep(0.2)

    def test_empty_scores_threshold_is_zero(self):
        gate = ConfidenceGate("top_prob")
        gate.calibrate([], coverage=0.7)
        assert gate.threshold == pytest.approx(0.0)
        assert gate.keep(0.0)

    def test_calibrate_stores_scores_for_frontier(self):
        gate = ConfidenceGate("top_prob")
        gate.calibrate([0.3, 0.7], coverage=0.5)
        assert gate._calib_scores == [0.3, 0.7]

    def test_gap_metric_calibration(self):
        gate = ConfidenceGate("gap")
        gate.calibrate([0.1, 0.2, 0.3, 0.4], coverage=0.5)
        # threshold = median([0.1,0.2,0.3,0.4]) = 0.25
        assert gate.keep(0.3)
        assert gate.keep(0.4)
        assert not gate.keep(0.1)

    def test_keep_at_threshold_boundary(self):
        gate = ConfidenceGate("top_prob")
        gate.calibrate([0.5], coverage=1.0)
        assert gate.keep(0.5)      # exactly at threshold → kept
        assert not gate.keep(0.4)  # below threshold → abstain
