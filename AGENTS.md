# RacingData Project - AI Agent Instructions

## Project Overview
A .NET 9.0 + Python ML pipeline: C# scrapes horse racing data from racingpost.com → a Python package (`race_analytics`) engineers features and runs prediction algorithms.

## Architecture

**Two-stage pipeline:**
1. **C# (`RaceDataDownloader`)** — CLI that scrapes racingpost.com → monthly `Results_YYYYMM.csv` files in `Data/`
2. **Python (`race_analytics/`)** — installable package; `features/` engineers features, `scripts/` generate predictions and run evaluations

**Python pipeline (in execution order):**
- `race_analytics/scripts/build_features.py` — runs `FeaturePipeline` (`race_analytics/features/pipeline.py`) over the last 7 months of `Results_YYYYMM.csv` → `Data/Race_Features.csv`, `Horse_Stats.csv`, `Jockey_Stats.csv`, `Trainer_Stats.csv`
- `race_analytics/scripts/predict.py` — reads those feature files + `TodaysRaceCards.csv`, calls `ACTIVE_ALGORITHM`, writes `Data/TodaysPredictions.csv`
- `race_analytics/scripts/evaluate.py` *(standalone)* — walk-forward evaluation (default 14 daily folds, `--folds N`); reads raw `Results_YYYYMM.csv` per fold and engineers features in-memory; writes a CSV only with `--save-results`/`--results-file`

Feature-engineering logic lives in `race_analytics/features/` (the source of truth). Notebooks in `race_analytics/notebooks/` are exploratory wrappers around `FeaturePipeline` — **not** part of the production pipeline; edit the `features/` module, not the notebooks.

**Algorithm registry** (`race_analytics/algorithms/__init__.py`): Central list of instantiated algorithm objects; one marked "active" for production use by `predict.py`.

## Verification & Feedback Loops

### After C# changes
```powershell
dotnet build && dotnet test
```

### After Python changes
```powershell
python -m pytest tests/
```

### After feature-engineering changes
Feature logic lives in `race_analytics/features/`. Rebuild the CSVs and check the console for errors:
```powershell
python -m race_analytics.scripts.build_features --data Data
```

### After algorithm changes — verify the contract
- `fit(train_df)` must not throw on well-formed input and must return `None`
- `predict(races, horse_stats, jockey_stats, trainer_stats=None)` must return at most one `{RaceId, HorseId}` row per qualifying race, no duplicates; races exceeding `max_horses` or with any null predictors are silently excluded
- `max_horses` filter must exclude races whose runner count exceeds the configured limit

### Full pipeline integration
```powershell
.\run.ps1
```
Builds C#, runs tests, downloads the last 365 days of results, then runs `build_features.py` → `predict.py`. Takes ~10 minutes. Use only for full integration verification.

## Critical Constraints

### Prediction-time data — no leakage
Two raw columns look usable but must never be features or filters: **RacingPostRating / TopSpeedRating** (`Results_*.csv`) are *post-race* figures (a TSR-gated model once faked 0.78 accuracy vs a 0.265 real anchor) — ratings may reach algorithms only as previous-race `LastRace*` values via the per-horse stats join, never the card; and **market odds** are unpopulated in `TodaysRaceCards.csv` at download (`FractionalOdds` = `"SP"`) — usable only to *measure* ROI retrospectively, never as a model input. Full detail: [`docs/data-pitfalls.md`](docs/data-pitfalls.md).

### racingpost.com scraping
Plain HTTP clients (`Invoke-WebRequest`, `curl`, `HttpClient` with default headers) get HTTP 429 from racingpost.com. The codebase uses `PuppeteerHtmlLoader` (headless Chrome, iPad Landscape emulation). For any ad-hoc probing of racingpost.com markup or selectors, drive it through `PuppeteerHtmlLoader` or a throwaway PuppeteerSharp script — not Invoke-WebRequest.

## CLI Command Structure
```
RaceDataDownloader.exe updateresults --output Data --period 365
RaceDataDownloader.exe todaysracecards --output Data
RaceDataDownloader.exe validate --output Data
```

## C# Conventions

### Command handler pattern
All CLI commands extend `FileCommandHandlerBase<THandler, TOptions>`:
```csharp
public class UpdateResultsCommandHandler : FileCommandHandlerBase<UpdateResultsCommandHandler, UpdateResultsOptions>
{
    protected override async Task InternalRunAsync(UpdateResultsOptions options)
    {
        var (start, end, dataFolder) = ValidateOptions(options);
        // implementation
    }
}
```

### HTML parser — optional fields
`HtmlNodeFinder.GetNode()` / `GetText()` throw when the element is absent.
Use `.Optional()` when a field may legitimately be missing on some race pages:
```csharp
// throws if absent — only use when the element is guaranteed present
_find.Anchor().WithAttribute("data-testid", "Link__Horse").GetText();

// returns null/empty when absent — use for optional fields
_find.Optional().Anchor().WithAttribute("data-testid", "Link__Going").GetText();
```

### Guard method naming
Methods that throw if a precondition isn't met should be named `EnsureXxx`
(e.g., `EnsureGoingDataIsPresent`). This mirrors .NET's own `EnsureSuccessStatusCode` convention.

### Data quality gates after scraping
Validation that detects a likely site structure change (e.g., all downloaded cards
missing a field that should always be present) must throw `ValidationException`,
not log a warning. A thrown exception causes `run.ps1` to halt visibly; a warning
is easy to miss in the log stream.

### Testing
- Snapshot tests use the Verify framework (`.verified.txt` files checked into source control)
- Test names: `{Class}Should.{Behavior}` (e.g., `UpdateResultsCommandHandlerShould.BackFillDataForMissingDays`)
- Mock HTTP with `MockHttpMessageHandler`; mock time via `IClock`

## Python Conventions

### Algorithm interface
All algorithms extend `BaseAlgorithm` (`race_analytics/algorithms/base.py`):
```python
# Regressors: extend RegressorAlgorithm, implement _create_model() (returns a sklearn estimator)
class MyRegressor(RegressorAlgorithm):
    def _create_model(self): ...

# Win-probability models: extend FieldPredictorBaseAlgorithm, implement predict_field().
# predict() is provided — returns the PredictedRank == 1 row per race: columns {RaceId, HorseId}
class MyClassifier(FieldPredictorBaseAlgorithm):
    def predict_field(self, races, horse_stats, jockey_stats, trainer_stats=None): ...

# Wrap any FieldPredictor in GatedClassifier to add a confidence gate (abstains below threshold).
```
Full class hierarchy and the registry (`ALGORITHMS`/`ACTIVE_ALGORITHM`): [`docs/evaluation-pipeline.md`](docs/evaluation-pipeline.md).

### Going encoding default
`encode_going()` in `race_analytics/features/transforms.py` defaults empty or null `Going`
values to `"Good"` before mapping. This ensures the model always receives a valid
one-hot going vector. Do not change this default without re-evaluating model performance —
the model was trained on data where going was always known.

### Testing
Tests live in `tests/` mirroring the `race_analytics/` package structure (e.g. `tests/utils/test_scoring.py`, `tests/algorithms/test_ridge_regression.py`). Follow the pattern in `test_data_analysis.py`: construct a small in-memory DataFrame, call the function, assert on output. Run with `python -m pytest tests/`.

## Evaluation Pipeline Design
Key decisions:
- `evaluate.py` loads raw `Results_YYYYMM.csv` per fold — does **not** read `Race_Features.csv`
- `predict.py` reads pre-computed feature files; still writes `TodaysPredictions.csv` for the downstream `validate` CLI step
- `KnownHorseAndJockey == True` filter applied by the pipeline before any algorithm sees data
- `max_horses` is a per-algorithm constructor parameter; applied internally by each algorithm
- Primary metric: winner accuracy; ROI displayed for information only
- Gated algorithms abstain on low-confidence races (trading coverage for accuracy/ROI); `evaluate.py` prints a ROI-vs-coverage frontier for them

Full methodology, the algorithm class hierarchy, filters, metric definitions, timing, and run commands: [`docs/evaluation-pipeline.md`](docs/evaluation-pipeline.md). Current active algorithm and latest measured results: `evaluations.md`.
