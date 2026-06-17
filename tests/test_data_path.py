from pathlib import Path

import pytest

from race_analytics.data_path import get_data_path


@pytest.fixture(autouse=True)
def _clear_env(  # pyright: ignore[reportUnusedFunction]  # collected by pytest, not called by name
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RACE_DATA_PATH", raising=False)


def test_default_resolves_to_data_dir_adjacent_to_package() -> None:
    result = Path(get_data_path())
    import race_analytics

    expected = Path(race_analytics.__file__).resolve().parent.parent / "Data"
    assert result == expected


def test_default_is_independent_of_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = Path(get_data_path())
    import race_analytics

    expected = Path(race_analytics.__file__).resolve().parent.parent / "Data"
    assert result == expected


def test_env_var_overrides_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("RACE_DATA_PATH", str(tmp_path))
    assert get_data_path() == str(tmp_path)


def test_empty_env_var_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RACE_DATA_PATH", "")
    result = Path(get_data_path())
    import race_analytics

    expected = Path(race_analytics.__file__).resolve().parent.parent / "Data"
    assert result == expected
