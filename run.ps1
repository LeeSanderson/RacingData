$ErrorActionPreference = "Stop"

function Invoke-NativeCommand() {
    # A handy way to run a command, and automatically throw an error if the
    # exit code is non-zero.

    if ($args.Count -eq 0) {
        throw "Must supply some arguments."
    }

    $command = $args[0]
    $commandArgs = @()
    if ($args.Count -gt 1) {
        $commandArgs = $args[1..($args.Count - 1)]
    }

    & $command $commandArgs
    $result = $LASTEXITCODE

    if ($result -ne 0) {
        throw "$command $commandArgs exited with code $result."
    } else {
        Write-Host "$command $commandArgs completed with exit code $result."
    }
}

$InitialPath = Resolve-Path "."
$RaceDownloaderPath = Join-Path $InitialPath "RaceDataDownloader\bin\Debug\net9.0"
$RaceDownloaderExe = Join-Path $RaceDownloaderPath "RaceDataDownloader.exe"
$RaceDataPath = Resolve-Path ".\Data"

Invoke-NativeCommand dotnet build
Invoke-NativeCommand dotnet test
## Invoke-NativeCommand $RaceDownloaderExe deduperesults --output $RaceDataPath
## Invoke-NativeCommand $RaceDownloaderExe fixraceids --output $RaceDataPath
Invoke-NativeCommand $RaceDownloaderExe updateresults --output $RaceDataPath --period 365
Invoke-NativeCommand $RaceDownloaderExe validate --output $RaceDataPath
Invoke-NativeCommand $RaceDownloaderExe todaysracecards --output $RaceDataPath

if (Get-Command uv -ErrorAction SilentlyContinue) {
    # Local dev venvs here are created by `uv` and ship without pip, so `python -m pip`
    # fails with "No module named pip". CI checks out fresh with no venv and no uv
    # install step, so it falls back to the hosted agent's system pip below.
    Invoke-NativeCommand uv pip install -e . --quiet
} else {
    Invoke-NativeCommand python -m pip install -e . --quiet
}

$env:RACE_DATA_PATH = $RaceDataPath

Invoke-NativeCommand python -m race_analytics.scripts.build_features --data $RaceDataPath

Invoke-NativeCommand python -m race_analytics.scripts.predict --data $RaceDataPath
