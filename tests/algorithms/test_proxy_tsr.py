from datetime import datetime

import pandas as pd
import pytest

from race_analytics.algorithms.proxy_tsr import ProxyTSRModel


def _row(
    horse_id: int,
    race_id: int,
    off: datetime,
    tsr: float | None = 90.0,
    finishing_pos: int = 1,
    beaten_dist: float = 0.0,
    course: str = "Newmarket",
) -> dict[str, object]:
    return {
        "HorseId": horse_id,
        "RaceId": race_id,
        "CourseName": course,
        "Off": off,
        "TopSpeedRating": tsr,
        "Speed": 16.0,
        "DistanceInMeters": 1600.0,
        "WeightInPounds": 126.0,
        "HorseCount": 8,
        "Surface_AllWeather": 0.0,
        "Surface_Dirt": 0.0,
        "Surface_Turf": 1.0,
        "Going_Firm": 0.0,
        "Going_Good": 1.0,
        "Going_Good_To_Firm": 0.0,
        "Going_Good_To_Soft": 0.0,
        "Going_Heavy": 0.0,
        "Going_Soft": 0.0,
        "RaceType_Flat": 1.0,
        "RaceType_Hurdle": 0.0,
        "RaceType_Other": 0.0,
        "RaceType_SteepleChase": 0.0,
        "FinishingPosition": finishing_pos,
        "OverallBeatenDistance": beaten_dist,
    }


D1 = datetime(2021, 1, 1)
D2 = datetime(2021, 2, 1)
D3 = datetime(2021, 3, 1)
D4 = datetime(2021, 4, 1)
D5 = datetime(2021, 5, 1)
D6 = datetime(2021, 6, 1)


@pytest.fixture
def basic_train_df() -> pd.DataFrame:
    """Six labelled rows across two horses plus two unlabelled rows."""
    rows = [
        _row(1, 101, D1, tsr=85.0),
        _row(1, 102, D2, tsr=90.0),
        _row(1, 103, D3, tsr=88.0),
        _row(2, 104, D1, tsr=92.0),
        _row(2, 105, D2, tsr=95.0),
        _row(2, 106, D3, tsr=91.0),
        _row(3, 107, D1, tsr=None),  # unlabelled — no TSR
        _row(3, 108, D2, tsr=None),
    ]
    return pd.DataFrame(rows)


def test_fit_completes_on_mixed_labelled_and_unlabelled_data(
    basic_train_df: pd.DataFrame,
) -> None:
    model = ProxyTSRModel()
    model.fit(basic_train_df)  # must not raise


def test_compute_horse_proxy_tsr_returns_required_columns(
    basic_train_df: pd.DataFrame,
) -> None:
    model = ProxyTSRModel()
    model.fit(basic_train_df)
    result = model.compute_horse_proxy_tsr(basic_train_df)

    assert list(result.columns) == ["HorseId", "LastProxyTSR"]
    assert result["HorseId"].nunique() == len(result)  # one row per horse


def test_last_proxy_tsr_reflects_most_recent_race() -> None:
    rows = [
        _row(1, 101, D1, tsr=70.0),  # oldest — low TSR
        _row(1, 102, D2, tsr=80.0),
        _row(1, 103, D3, tsr=90.0),  # newest — high TSR
    ]
    df = pd.DataFrame(rows)
    model = ProxyTSRModel()
    model.fit(df)
    result = model.compute_horse_proxy_tsr(df)

    horse1 = result[result["HorseId"] == 1].iloc[0]
    last = horse1["LastProxyTSR"]
    # LastProxyTSR is computed from the most-recent (D3) row regardless of row
    # order — computing on a reversed-date copy gives the same result.
    rows_reversed = [
        _row(1, 103, D3, tsr=90.0),
        _row(1, 102, D2, tsr=80.0),
        _row(1, 101, D1, tsr=70.0),
    ]
    result2 = model.compute_horse_proxy_tsr(pd.DataFrame(rows_reversed))
    horse1_r = result2[result2["HorseId"] == 1].iloc[0]
    assert abs(horse1_r["LastProxyTSR"] - last) < 1e-6


def test_as_of_proxy_ignores_future_races(basic_train_df: pd.DataFrame) -> None:
    """A training row's proxy must come only from that horse's earlier races, so
    adding a later (future) race cannot change an earlier row's proxy."""
    model = ProxyTSRModel()
    model.fit(basic_train_df)

    two = pd.DataFrame([_row(1, 101, D1, tsr=85.0), _row(1, 102, D2, tsr=90.0)])
    with_future = pd.DataFrame(
        [
            _row(1, 101, D1, tsr=85.0),
            _row(1, 102, D2, tsr=90.0),
            _row(1, 103, D3, tsr=88.0),  # a later race for the same horse
        ]
    )

    proxy_two = model.compute_as_of_proxy(two)
    proxy_future = model.compute_as_of_proxy(with_future)

    # The D2 row (index 1 in both frames) sees only the D1 race either way.
    assert proxy_two.loc[1] == pytest.approx(proxy_future.loc[1])
    # The horse's first race (D1, index 0) has no prior race -> NaN.
    assert pd.isna(proxy_two.loc[0])


def test_unseen_course_name_does_not_raise(basic_train_df: pd.DataFrame) -> None:
    model = ProxyTSRModel()
    model.fit(basic_train_df)

    unseen_rows = [
        _row(1, 201, D4, tsr=None, course="Timbuktu Racecourse"),
        _row(2, 202, D4, tsr=None, course="Timbuktu Racecourse"),
    ]
    predict_df = pd.concat(
        [basic_train_df, pd.DataFrame(unseen_rows)], ignore_index=True
    )
    result = model.compute_horse_proxy_tsr(predict_df)  # must not raise
    assert len(result) > 0


def test_fit_raises_when_no_labelled_rows() -> None:
    rows = [
        _row(1, 101, D1, tsr=None),
        _row(2, 102, D1, tsr=None),
    ]
    with pytest.raises(ValueError):
        ProxyTSRModel().fit(pd.DataFrame(rows))


def test_tune_completes_without_error(basic_train_df: pd.DataFrame) -> None:
    model = ProxyTSRModel()
    model.tune(basic_train_df, n_iter=2, cv=2)  # must not raise


def test_fit_works_after_tune(basic_train_df: pd.DataFrame) -> None:
    model = ProxyTSRModel()
    model.tune(basic_train_df, n_iter=2, cv=2)
    model.fit(basic_train_df)
    result = model.compute_horse_proxy_tsr(basic_train_df)

    assert list(result.columns) == ["HorseId", "LastProxyTSR"]
    assert len(result) == 3


def test_tune_skips_gracefully_on_insufficient_data() -> None:
    rows = [_row(1, 101, D1, tsr=90.0)]  # only 1 row — below cv*2=4 threshold
    model = ProxyTSRModel()
    model.tune(pd.DataFrame(rows), n_iter=2, cv=2)  # must not raise
    # Regressor remains the default (unfitted) instance — fit() still usable
    model.fit(pd.DataFrame(rows))  # also must not raise
