# Refactor Candidates

After a TDD cycle, look for:

- **Duplication** → Extract a method or helper. The `FileSystemExtensions`, `StringExtensions`, and `RacingDataDownloaderExtensions` files in this project are the natural home for cross-handler helpers.
- **Long methods** → Break into private helpers (keep tests on the public `RunAsync` / `Parse` interface). `UpdateMonthlyResultsFile` is a good model: pulled out of `InternalRunAsync` but not exposed.
- **Shallow modules** → Combine or [deepen](deep-modules.md). Watch for parser helpers that only exist to be called once.
- **Feature envy** → Move logic to where the data lives. A method on `UpdateResultsCommandHandler` that mostly reads from `RaceResultRecord` belongs on (or near) `RaceResultRecord`.
- **Primitive obsession** → Introduce value objects. The project already does this with `RaceDistance`, `RaceWeight`, `RaceClassification`, `DateRange` — prefer adding to that vocabulary rather than passing tuples of primitives.
- **Existing code** that the new code reveals as problematic — note it, raise it as a follow-up issue under `issues/`, don't expand scope mid-cycle.

After each refactor step run `dotnet test` (fast) or `.\run.ps1` (full pipeline). Verified snapshots may need updating — review the `.received.txt` vs `.verified.txt` diff carefully and rename only when the new output is actually what you wanted.
