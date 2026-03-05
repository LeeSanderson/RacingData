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

try {
    Invoke-NativeCommand dotnet build
    Invoke-NativeCommand dotnet test
    ## Invoke-NativeCommand $RaceDownloaderExe deduperesults --output $RaceDataPath
    ## Invoke-NativeCommand $RaceDownloaderExe fixraceids --output $RaceDataPath
    Invoke-NativeCommand $RaceDownloaderExe updateresults --output $RaceDataPath --period 365
    Invoke-NativeCommand $RaceDownloaderExe validate --output $RaceDataPath
    Invoke-NativeCommand $RaceDownloaderExe todaysracecards --output $RaceDataPath

    Invoke-NativeCommand python -m pip install nbconvert --quiet
    Invoke-NativeCommand python -m pip install ipykernel --quiet
    Invoke-NativeCommand python -m pip install numpy --quiet
    Invoke-NativeCommand python -m pip install Pandas --quiet
    Invoke-NativeCommand python -m pip install matplotlib --quiet
    Invoke-NativeCommand python -m pip install scikit-learn --quiet
    Invoke-NativeCommand python -m pip install ipywidgets --quiet

    Set-Location $RaceDataPath
    Invoke-NativeCommand python -m nbconvert --to script "FeatureAnalysis.ipynb"
    Invoke-NativeCommand python "FeatureAnalysis.py"

    Invoke-NativeCommand python -m nbconvert --to script "HorseStatsBuilder.ipynb"
    Invoke-NativeCommand python "HorseStatsBuilder.py"

    Invoke-NativeCommand python -m nbconvert --to script "JockeyStatsBuilder.ipynb"
    Invoke-NativeCommand python "JockeyStatsBuilder.py"

    Invoke-NativeCommand python -m nbconvert --to script "LinearRegressionPredictor.ipynb"
    Invoke-NativeCommand python "LinearRegressionPredictor.py"
} finally {
    Set-Location $InitialPath
}
