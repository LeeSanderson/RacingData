# RacingData Project - AI Agent Instructions

## Project Overview
This is a .NET 9.0 horse racing data pipeline that extracts, processes, and feeds race data to machine learning algorithms for prediction. The system follows a two-stage architecture: C# data extraction → Python ML processing.

## Architecture & Data Flow

### Core Components
- **RacePredictor.Core**: Domain models (`RaceEntity`, `RaceCard`, `RaceResult`, `RaceAttributes`)
- **RaceDataDownloader**: CLI tool with command handlers for web scraping racingpost.com
- **Data/**: Python notebooks for feature engineering and ML prediction

### Data Pipeline Workflow
1. **Extraction**: CLI downloads race results/cards from racingpost.com into monthly CSV files (`Results_YYYYMM.csv`)
2. **Processing**: Python notebooks convert raw data into features (`Horse_Stats.csv`, `Jockey_Stats.csv`, `Race_Features.csv`) 
3. **Prediction**: Linear regression models generate race predictions (`Predictions.json`, `TodaysPredictions.csv`)

## Critical Development Workflows

### Main Build & Test Pipeline
Use the `run.ps1` script for complete pipeline execution:
```powershell
.\run.ps1  # Builds C#, runs tests, downloads data, executes Python notebooks
```

### CLI Command Structure
All commands follow the pattern: `RaceDataDownloader.exe <verb> <options>`
- `updateresults --output Data --period 365`: Download last 365 days of race results
- `todaysracecards --output Data`: Get today's race cards for prediction
- `validate --output Data`: Validate predictions against actual results

### Project-Specific Build Commands
- Use VS Code tasks: `build`, `publish`, `watch` (prefer over direct dotnet commands)
- Python notebooks: Auto-converted to `.py` files and executed by `run.ps1`

## Code Patterns & Conventions

### Command Handler Pattern
All CLI commands inherit from `FileCommandHandlerBase<THandler, TOptions>`:
```csharp
public class UpdateResultsCommandHandler : FileCommandHandlerBase<UpdateResultsCommandHandler, UpdateResultsOptions>
{
    protected override async Task InternalRunAsync(UpdateResultsOptions options)
    {
        var (start, end, dataFolder) = ValidateOptions(options);
        // Implementation logic
    }
}
```

### Testing Conventions
- Use Verify framework for snapshot testing (`.verified.txt` files)
- Test data mocking with NSubstitute + MockHttpMessageHandler
- Name tests as `{Class}Should.{Behavior}.{ExpectedOutcome}` (e.g., `UpdateResultsCommandHandlerShould.BackFillDataForThe11ThWhenGetting2DaysOfDataAndTodayIs13ThAndHaveExistingDataFor12Th`)

### Data Models
- Immutable record types with constructor validation
- Entity pattern: `RaceEntity(int id, string name)` for courses, races
- Results vs Cards: `RaceResult` (historical) vs `RaceCard` (upcoming races)

### File Organization
- Monthly CSV files: `Results_YYYYMM.csv` in `Data/` folder
- JSON + CSV dual output for most data exports
- Python notebooks co-located with generated `.py` files

## Integration Points

### External Dependencies
- **racingpost.com**: Primary data source (HTTP scraping with retry logic)
- **Python ML Stack**: pandas, scikit-learn, matplotlib for feature engineering
- **File System Abstractions**: All file operations mockable via `IFileSystem`

### Cross-Component Communication
- CLI outputs structured CSV/JSON consumed by Python notebooks
- Dependency injection with HttpClientFactory for external calls
- IClock abstraction enables time-based testing

## Data Schema Insights
Race result CSV columns include: CourseId, RaceName, Position, Course, DateTime, RaceClass, AgeRestriction, Distance, Going, Surface, HorseId, HorseName, JockeyId, etc.

Feature files track statistics: win rates, earnings, recent form for horses/jockeys.
