import os
from pathlib import Path


def get_data_path() -> str:
    """Return the directory containing race data CSVs/JSON.

    Honors the RACE_DATA_PATH environment variable when set (used by run.ps1
    to pass an explicit path). Otherwise defaults to the 'Data' directory
    adjacent to the installed race_analytics package, which works for
    interactive notebook runs from any working directory.
    """
    env = os.environ.get("RACE_DATA_PATH")
    if env:
        return env
    package_dir = Path(__file__).resolve().parent
    return str(package_dir.parent / "Data")
