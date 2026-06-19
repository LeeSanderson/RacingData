import numpy as np
import pandas as pd

from race_analytics.scripts.backtest_staking import (
    _attach_stakes,  # pyright: ignore[reportPrivateUsage]  # test exercises the module's private pure helper
    _backtest,  # pyright: ignore[reportPrivateUsage]  # test exercises the module's private pure helper
    _identify_picks,  # pyright: ignore[reportPrivateUsage]  # test exercises the module's private pure helper
    _summarise,  # pyright: ignore[reportPrivateUsage]  # test exercises the module's private pure helper
)

# ================================================================
# Fixture: a tiny eval-results-shaped frame. Stakes use the production default
# BANKROLL (calibrated to ≈ £1 median), so the value bet below is sized as a
# modest sub-cap bet rather than a strong edge that would clip at the £5 CAP.
#
# Race 1 (value bet, pick WINS):
#   Horse A: WinProbability 0.40 -> ModelProb 0.40, MarketProb 0.30 -> edge 0.10 > MIN_EDGE
#            odds 3.0 -> f* = (0.40*3-1)/(3-1) = 0.1 -> stake 0.25*0.1*120 = 3.00
#   Horse B: WinProbability 0.35 -> ModelProb 0.35, MarketProb 0.35 -> edge 0 -> no bet
#   Horse C: WinProbability 0.25 -> ModelProb 0.25, MarketProb 0.35 -> edge -0.10 -> no bet
#   Pick = A (highest prob), FinishingPosition 1, odds 3.0.
# Race 2 (no value, pick LOSES):
#   Horse D: WinProbability 0.55 -> ModelProb 0.55, MarketProb 0.55 -> edge 0 -> no bet
#   Horse E: WinProbability 0.45 -> ModelProb 0.45, MarketProb 0.45 -> edge 0 -> no bet
#   Pick = D (highest prob), FinishingPosition 3, odds 4.0.
# ================================================================


def _fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "FoldDate": "2026-01-01",
                "Algorithm": "Algo",
                "RaceId": 1,
                "HorseId": 10,
                "WinProbability": 0.40,
                "PredictedScore": np.nan,
                "MarketProb": 0.30,
                "ResolvedOdds": 3.0,
                "FinishingPosition": 1,
            },
            {
                "FoldDate": "2026-01-01",
                "Algorithm": "Algo",
                "RaceId": 1,
                "HorseId": 11,
                "WinProbability": 0.35,
                "PredictedScore": np.nan,
                "MarketProb": 0.35,
                "ResolvedOdds": 5.0,
                "FinishingPosition": 2,
            },
            {
                "FoldDate": "2026-01-01",
                "Algorithm": "Algo",
                "RaceId": 1,
                "HorseId": 12,
                "WinProbability": 0.25,
                "PredictedScore": np.nan,
                "MarketProb": 0.35,
                "ResolvedOdds": 4.0,
                "FinishingPosition": 3,
            },
            {
                "FoldDate": "2026-01-01",
                "Algorithm": "Algo",
                "RaceId": 2,
                "HorseId": 20,
                "WinProbability": 0.55,
                "PredictedScore": np.nan,
                "MarketProb": 0.55,
                "ResolvedOdds": 4.0,
                "FinishingPosition": 3,
            },
            {
                "FoldDate": "2026-01-01",
                "Algorithm": "Algo",
                "RaceId": 2,
                "HorseId": 21,
                "WinProbability": 0.45,
                "PredictedScore": np.nan,
                "MarketProb": 0.45,
                "ResolvedOdds": 6.0,
                "FinishingPosition": 1,
            },
        ]
    )


# ================================================================
# _attach_stakes — reuses the production compute_stakes
# ================================================================


def test_attach_stakes_sizes_the_value_bet_and_zeroes_the_rest() -> None:
    staked = _attach_stakes(_fixture())
    by_horse = staked.set_index("HorseId")["Stake"]
    assert by_horse[10] == 3.00  # value bet, full-field-normalized Kelly (sub-cap)
    assert by_horse[11] == 0.0  # no edge
    assert by_horse[12] == 0.0  # negative edge
    assert by_horse[20] == 0.0  # no edge
    assert by_horse[21] == 0.0  # no edge


# ================================================================
# _identify_picks — one rank-1 pick per race, carrying its stake
# ================================================================


def test_identify_picks_takes_highest_probability_horse_with_its_stake() -> None:
    picks = _identify_picks(_attach_stakes(_fixture()))
    assert len(picks) == 2  # one per race
    by_race = picks.set_index("RaceId")
    assert by_race.loc[1, "HorseId"] == 10  # highest prob in race 1
    assert by_race.loc[1, "Stake"] == 3.00  # carries the value-bet stake
    assert by_race.loc[2, "HorseId"] == 20  # highest prob in race 2
    assert by_race.loc[2, "Stake"] == 0.0  # no-bet pick


# ================================================================
# _summarise — flat-£1 vs Kelly ROI, coverage, stake distribution
# ================================================================

_SUMMARY_FIELDS = {
    "races",
    "flat_profit",
    "flat_roi",
    "bets",
    "coverage",
    "kelly_profit",
    "kelly_roi",
    "stake_median",
    "stake_mean",
    "stake_p10",
    "stake_p25",
    "stake_p75",
    "stake_p90",
    "stake_min",
    "stake_max",
}


def test_summarise_reports_all_expected_fields() -> None:
    summary = _summarise(_identify_picks(_attach_stakes(_fixture())))
    assert set(summary) >= _SUMMARY_FIELDS


def test_summarise_flat_roi_matches_hand_computed_value() -> None:
    summary = _summarise(_identify_picks(_attach_stakes(_fixture())))
    # Picks: race 1 winner @ 3.0 -> +2.0; race 2 loser -> -1.0. Net +1.0 over 2 picks.
    assert summary["races"] == 2
    assert summary["flat_profit"] == 1.0
    assert summary["flat_roi"] == 0.5


def test_summarise_coverage_is_a_valid_fraction() -> None:
    summary = _summarise(_identify_picks(_attach_stakes(_fixture())))
    assert summary["bets"] == 1  # only the value bet is staked
    assert 0.0 <= summary["coverage"] <= 1.0
    assert summary["coverage"] == 0.5


def test_summarise_kelly_roi_uses_staked_returns() -> None:
    summary = _summarise(_identify_picks(_attach_stakes(_fixture())))
    # Only the 3.00 value bet is live: it wins at 3.0 -> profit 3.00*(3-1) = 6.0.
    assert summary["kelly_profit"] == 6.0
    assert summary["kelly_roi"] == 2.0  # 6.0 / 3.00 staked
    assert summary["stake_median"] == 3.00
    assert summary["stake_mean"] == 3.00


def test_summarise_handles_no_bets_without_dividing_by_zero() -> None:
    # A frame whose only pick fails the value gate -> zero coverage.
    fixture = _fixture()
    no_value = fixture[fixture["RaceId"] == 2].copy()  # only race 2 (no edge anywhere)
    summary = _summarise(_identify_picks(_attach_stakes(no_value)))
    assert summary["bets"] == 0
    assert summary["coverage"] == 0.0
    assert np.isnan(summary["kelly_roi"])
    assert summary["kelly_profit"] == 0.0


def test_summarise_empty_picks_is_safe() -> None:
    summary = _summarise(_identify_picks(_attach_stakes(_fixture().iloc[0:0].copy())))
    assert summary["races"] == 0
    assert summary["coverage"] == 0.0


# ================================================================
# _backtest — one summary per algorithm, no cross-algorithm normalization
# ================================================================


def test_attach_stakes_zeroes_when_staking_columns_are_absent() -> None:
    # Older eval files (pre-MarketProb) lack WinProbability/MarketProb/ResolvedOdds.
    legacy = pd.DataFrame(
        [
            {
                "FoldDate": "2026-01-01",
                "Algorithm": "Algo",
                "RaceId": 1,
                "HorseId": 10,
                "PredictedScore": 17.0,
                "DecimalOdds": 3.0,
                "FinishingPosition": 1,
            }
        ]
    )
    staked = _attach_stakes(legacy)
    assert (staked["Stake"] == 0.0).all()  # no crash, no bets


def test_summarise_falls_back_to_decimal_odds_when_resolved_absent() -> None:
    # ResolvedOdds == DecimalOdds on SP-only history; the flat baseline still computes.
    picks = pd.DataFrame(
        [
            {
                "FoldDate": "2026-01-01",
                "Algorithm": "Algo",
                "RaceId": 1,
                "HorseId": 10,
                "DecimalOdds": 3.0,
                "FinishingPosition": 1,
                "Stake": 0.0,
            }
        ]
    )
    summary = _summarise(picks)
    assert summary["races"] == 1
    assert summary["flat_profit"] == 2.0  # winner @ 3.0 -> +2.0
    assert summary["bets"] == 0


def test_backtest_summarises_each_algorithm_independently() -> None:
    # Two algorithms share RaceId 1. If stakes were normalized across both
    # algorithms at once, the within-race ModelProb would be halved and the edge
    # would collapse below MIN_EDGE. Per-algorithm normalization keeps the bet.
    df = pd.concat([_fixture(), _fixture().assign(Algorithm="Other")])
    summaries = _backtest(df)
    assert set(summaries) == {"Algo", "Other"}
    assert summaries["Algo"]["bets"] == 1
    assert summaries["Other"]["bets"] == 1
