---
name: tdd
description: Test-driven development with red-green-refactor loop. Use when user wants to build features or fix bugs using TDD, mentions "red-green-refactor", wants integration tests, or asks for test-first development.
---

# Test-Driven Development

## Project context

This codebase has two test surfaces:

- **C# (RacePredictor.Core.Tests, RaceDataDownloader.Tests)** — xUnit + FluentAssertions + NSubstitute + Verify (snapshot tests) + `RichardSzalay.MockHttp`. Tests are named `{Class}Should.{Behavior}`. The `MockFileSystemBuilder` and `MockRacingDataDownloader` helpers exist to wire up the standard system-boundary mocks. Verified snapshots live alongside tests as `.verified.txt` files.
- **Python (Data/)** — feature-engineering and prediction notebooks. There is no formal test runner today; the pragmatic equivalent is running `run.ps1` end-to-end and inspecting the generated `Horse_Stats.csv`, `Jockey_Stats.csv`, `Race_Features.csv`, `Predictions.json`. When adding non-trivial Python logic, pull it into a pure function that takes a `DataFrame` in and returns a `DataFrame` out, so it can be exercised with pytest against a small fixture CSV.

## Philosophy

**Core principle**: Tests should verify behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't.

**Good tests** are integration-style: they exercise real code paths through public APIs. The command-handler tests in this project are the model — they call `RunAsync` and assert on the CSV content captured by the mock filesystem. They describe _what_ the system does, not _how_.

**Bad tests** are coupled to implementation. They mock internal collaborators (the parsers, the node finder), assert on `Received(n)` call counts for things that aren't true boundaries, or independently invoke a parser to verify a handler.

See [tests.md](tests.md) for good vs bad examples and [mocking.md](mocking.md) for where the system boundaries actually are (`IHtmlLoader`, `IFileSystem`, `IClock`, `IRacingDataDownloader`).

## Anti-Pattern: Horizontal Slices

**DO NOT write all tests first, then all implementation.** This is "horizontal slicing" — treating RED as "write all tests" and GREEN as "write all code."

This produces **crap tests**:

- Tests written in bulk test _imagined_ behavior, not _actual_ behavior
- You end up testing the _shape_ of things (data structures, function signatures) rather than user-facing behavior
- Tests become insensitive to real changes — they pass when behavior breaks, fail when behavior is fine
- You outrun your headlights, committing to test structure before understanding the implementation

**Correct approach**: Vertical slices via tracer bullets. One test → one implementation → repeat. Each test responds to what you learned from the previous cycle. Because you just wrote the code, you know exactly what behavior matters and how to verify it.

```
WRONG (horizontal):
  RED:   test1, test2, test3, test4, test5
  GREEN: impl1, impl2, impl3, impl4, impl5

RIGHT (vertical):
  RED→GREEN: test1→impl1
  RED→GREEN: test2→impl2
  RED→GREEN: test3→impl3
  ...
```

## Workflow

### 1. Planning

Before writing any code:

- [ ] Confirm with user what interface changes are needed (e.g. a new command handler under `RaceDataDownloader/Commands/`, or a new parser in `RacePredictor.Core.RacingPost/`)
- [ ] Confirm with user which behaviors to test (prioritize)
- [ ] Identify opportunities for [deep modules](deep-modules.md) (small interface, deep implementation — the existing parsers are good examples)
- [ ] Design interfaces for [testability](interface-design.md)
- [ ] List the behaviors to test (not implementation steps)
- [ ] Get user approval on the plan

Ask: "What should the public interface look like? Which behaviors are most important to test?"

**You can't test everything.** Confirm with the user exactly which behaviors matter most. Focus testing effort on critical paths and complex logic, not every possible edge case.

### 2. Tracer Bullet

Write ONE test that confirms ONE thing about the system:

```
RED:   Write test for first behavior → test fails
GREEN: Write minimal code to pass → test passes
```

For a new command handler, the tracer bullet is usually the happy-path "downloads and writes the expected CSV" test, verified via `await Verify(_mockFileSystemBuilder.GetContent(...))`.

### 3. Incremental Loop

For each remaining behavior:

```
RED:   Write next test → fails
GREEN: Minimal code to pass → passes
```

Rules:

- One test at a time
- Only enough code to pass current test
- Don't anticipate future tests
- Keep tests focused on observable behavior

### 4. Refactor

After all tests pass, look for [refactor candidates](refactoring.md):

- [ ] Extract duplication (often into `FileSystemExtensions`, `StringExtensions`, or a new helper)
- [ ] Deepen modules (move complexity behind simple interfaces)
- [ ] Apply SOLID principles where natural
- [ ] Consider what new code reveals about existing code
- [ ] Run `dotnet test` (or `.\run.ps1` for the full pipeline) after each refactor step

**Never refactor while RED.** Get to GREEN first.

## Checklist Per Cycle

```
[ ] Test describes behavior, not implementation
[ ] Test uses public interface only (e.g. RunAsync, Parse, build_*)
[ ] Test would survive internal refactor
[ ] Code is minimal for this test
[ ] No speculative features added
```
