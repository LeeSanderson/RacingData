import pandas as pd
import pytest

from race_analytics.betting.staking import (
    compute_stakes,
    kelly_fraction,
    normalize_within_race,
)


def test_normalize_makes_each_race_sum_to_one() -> None:
    # Un-normalized per-horse WinProbability summing to 1.5 within the race; dividing by
    # the per-race total turns it into a true within-race distribution summing to 1.
    field = pd.DataFrame(
        {
            "RaceId": [1, 1, 1],
            "WinProbability": [0.9, 0.3, 0.3],
        }
    )
    model_prob = normalize_within_race(field)
    assert model_prob.tolist() == pytest.approx([0.6, 0.2, 0.2])
    assert model_prob.sum() == pytest.approx(1.0)


def test_kelly_fraction_matches_the_formula() -> None:
    # f* = (p·O - 1) / (O - 1). For p=0.5, O=3.0 -> (1.5-1)/2 = 0.25.
    model_prob = pd.Series([0.5, 0.4])
    odds = pd.Series([3.0, 5.0])
    f_star = kelly_fraction(model_prob, odds)
    assert f_star.tolist() == pytest.approx([0.25, (0.4 * 5 - 1) / 4])


def test_kelly_fraction_is_nan_for_unusable_odds() -> None:
    # Odds missing or not greater than 1 make the divisor (O-1) ≤ 0 / undefined -> NaN.
    model_prob = pd.Series([0.5, 0.5, 0.5])
    odds = pd.Series([float("nan"), 1.0, 0.5])
    f_star = kelly_fraction(model_prob, odds)
    assert f_star.isna().all()


def test_positive_edge_pick_gets_a_positive_stake_negative_edge_gets_zero() -> None:
    # WinProbability [0.6, 0.2] -> ModelProb [0.75, 0.25]. Runner 0 beats its market
    # price (edge 0.25), runner 1 is below it (edge -0.25 -> no bet).
    # f*_0 = (0.75·3 - 1)/(3 - 1) = 0.625; stake = 0.2 · 0.625 · 10 = 1.25.
    field = pd.DataFrame(
        {
            "RaceId": [1, 1],
            "WinProbability": [0.6, 0.2],
            "MarketProb": [0.5, 0.5],
            "ResolvedOdds": [3.0, 2.0],
        }
    )
    stakes = compute_stakes(field, kelly_frac=0.2, bankroll=10.0, cap=100.0)
    assert stakes.tolist() == pytest.approx([1.25, 0.0])


def test_edge_at_or_below_min_edge_is_no_bet() -> None:
    # ModelProb [0.52, 0.48] vs MarketProb [0.50, 0.50] -> edge 0.02, below the default
    # MIN_EDGE of 0.03, so neither runner is backed despite usable odds.
    field = pd.DataFrame(
        {
            "RaceId": [1, 1],
            "WinProbability": [0.52, 0.48],
            "MarketProb": [0.50, 0.50],
            "ResolvedOdds": [3.0, 3.0],
        }
    )
    assert compute_stakes(field).tolist() == pytest.approx([0.0, 0.0])


def test_missing_or_short_odds_force_zero_stake_even_with_a_strong_edge() -> None:
    # Three single-runner races, each with a 0.5 edge (ModelProb 1.0 vs MarketProb 0.5)
    # but an unusable price: missing, exactly evens, and below 1. All stake 0.
    field = pd.DataFrame(
        {
            "RaceId": [1, 2, 3],
            "WinProbability": [0.4, 0.4, 0.4],
            "MarketProb": [0.5, 0.5, 0.5],
            "ResolvedOdds": [float("nan"), 1.0, 0.5],
        }
    )
    assert compute_stakes(field).tolist() == pytest.approx([0.0, 0.0, 0.0])


def test_stake_is_capped() -> None:
    # A short-priced, high-confidence pick: ModelProb 1.0, edge 0.5, f* = 1.0, so the
    # raw stake 0.25·1·100 = £25 is clipped to the default £5 CAP.
    field = pd.DataFrame(
        {
            "RaceId": [1],
            "WinProbability": [0.4],
            "MarketProb": [0.5],
            "ResolvedOdds": [3.0],
        }
    )
    assert compute_stakes(field, bankroll=100.0).tolist() == pytest.approx([5.0])


def test_payout_uses_gross_odds_while_judgement_uses_market_prob() -> None:
    # Identical edge for both runners (ModelProb 0.5, MarketProb 0.4) but different gross
    # prices. The bigger price -> bigger Kelly stake, proving the payout term uses the
    # gross odds O, not the de-overrounded MarketProb both runners share.
    # f*_0 = (0.5·4 - 1)/3 = 1/3 -> 0.2·(1/3)·30 = 2.0;
    # f*_1 = (0.5·2.5 - 1)/1.5 = 1/6 -> 0.2·(1/6)·30 = 1.0.
    field = pd.DataFrame(
        {
            "RaceId": [1, 1],
            "WinProbability": [0.6, 0.6],
            "MarketProb": [0.4, 0.4],
            "ResolvedOdds": [4.0, 2.5],
        }
    )
    stakes = compute_stakes(field, kelly_frac=0.2, bankroll=30.0, cap=100.0)
    assert stakes.tolist() == pytest.approx([2.0, 1.0])


def test_value_gate_uses_de_overrounded_market_prob_not_the_gross_price() -> None:
    # ModelProb 0.52, gross odds 2.0 (gross-implied 0.50 -> edge 0.02, below MIN_EDGE),
    # but the overround-removed MarketProb is 0.45 -> edge 0.07, above MIN_EDGE. Judging
    # on MarketProb (the de-overround half of the split) backs the bet; judging on the
    # gross-implied price would have gated it out. f* = (0.52·2 - 1)/1 = 0.04.
    field = pd.DataFrame(
        {
            "RaceId": [1, 1],
            "WinProbability": [0.52, 0.48],
            "MarketProb": [0.45, 0.55],
            "ResolvedOdds": [2.0, 2.0],
        }
    )
    stakes = compute_stakes(field, bankroll=100.0)
    assert stakes.tolist() == pytest.approx([1.0, 0.0])


def test_stakes_are_rounded_to_two_decimal_places() -> None:
    # f* = (0.5·4 - 1)/3 = 1/3, so the raw stake 0.25·(1/3)·10 = 0.8333… rounds to 0.83.
    field = pd.DataFrame(
        {
            "RaceId": [1, 1],
            "WinProbability": [0.5, 0.5],
            "MarketProb": [0.4, 0.4],
            "ResolvedOdds": [4.0, 4.0],
        }
    )
    assert compute_stakes(field, bankroll=10.0).tolist() == pytest.approx([0.83, 0.83])


def test_default_bankroll_is_calibrated_to_a_roughly_one_pound_typical_stake() -> None:
    # issues/005: BANKROLL is calibrated from the diagnostic backtest's stake distribution
    # so the typical advised stake lands near the familiar £1 unit (PRD user story 5), not
    # the sub-£1 placeholder the provisional BANKROLL=25 produced. A representative value
    # bet (ModelProb 0.52 vs de-overrounded MarketProb 0.48 -> edge 0.04, gross odds 2.0,
    # f* = (0.52·2 - 1)/(2 - 1) = 0.04) must therefore stake on the order of £1 at the
    # *default* bankroll — it stakes only ~£0.25 at the old provisional 25.
    field = pd.DataFrame(
        {
            "RaceId": [1, 1],
            "WinProbability": [0.52, 0.48],
            "MarketProb": [0.48, 0.52],
            "ResolvedOdds": [2.0, 2.0],
        }
    )
    top_stake = compute_stakes(field).iloc[0]
    assert 0.5 <= top_stake <= 2.0


def test_normalization_is_per_race_across_a_multi_race_frame() -> None:
    # Race 1's WinProbability sums to 0.8 (-> ModelProb [0.75, 0.25]) and race 2's to 1.0
    # (-> [0.5, 0.5]); each race must normalize on its own total, not the frame's.
    # Race 1 winner: f* = (0.75·3 - 1)/2 = 0.625 -> 0.2·0.625·10 = 1.25.
    # Race 2 winner: f* = (0.5·4 - 1)/3 = 1/3 -> 0.2·(1/3)·10 = 0.6667 -> 0.67.
    field = pd.DataFrame(
        {
            "RaceId": [1, 1, 2, 2],
            "WinProbability": [0.6, 0.2, 0.5, 0.5],
            "MarketProb": [0.5, 0.5, 0.3, 0.7],
            "ResolvedOdds": [3.0, 3.0, 4.0, 4.0],
        }
    )
    stakes = compute_stakes(field, kelly_frac=0.2, bankroll=10.0, cap=100.0)
    assert stakes.tolist() == pytest.approx([1.25, 0.0, 0.67, 0.0])
