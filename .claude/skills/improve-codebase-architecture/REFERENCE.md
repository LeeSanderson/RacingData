# Reference

## Dependency Categories

When assessing a candidate for deepening, classify its dependencies:

### 1. In-process

Pure computation, in-memory state, no I/O. Always deepenable — just merge the modules and test directly.

Examples in this codebase: `RacingResultParser`, `RaceCardParser`, `RunnerParser`, `RaceCardRunnerParser`, `HtmlNodeFinder`, `LengthsPerSecondScaleTable`, `DateRange`, `StringExtensions`. Python pure transforms over a `DataFrame` (e.g. an extracted `build_horse_stats(races)` function) are in-process too.

### 2. Local-substitutable

Dependencies that have local test stand-ins. Deepenable if the test substitute exists. The deepened module is tested with the local stand-in running in the test suite.

In this codebase the canonical example is `IFileSystem` from `System.IO.Abstractions` — production uses the real `FileSystem`, tests use `MockFileSystemBuilder` (an NSubstitute-backed in-memory stand-in that captures `WriteAllTextAsync` content into a dictionary). `IClock` is also local-substitutable (`RealClock` vs `Substitute.For<IClock>()`).

### 3. Remote but owned (Ports & Adapters)

Your own services across a network boundary (microservices, internal APIs). Define a port (interface) at the module boundary. The deep module owns the logic; the transport is injected. Tests use an in-memory adapter. Production uses the real HTTP/gRPC/queue adapter.

This pattern is not heavily used today since the project is a self-contained pipeline, but the shape is mirrored by `IHtmlLoader` (port) with `HttpClientHtmlLoader` and `PuppeteerHtmlLoader` as production adapters and a fake/string-returning loader as the test adapter.

Recommendation shape: "Define a shared interface (port), implement an HTTP adapter for production and an in-memory adapter for testing, so the logic can be tested as one deep module even though it's deployed across a network boundary."

### 4. True external (Mock)

Third-party services you don't control. Mock at the boundary. The deepened module takes the external dependency as an injected port, and tests provide a mock implementation.

In this codebase the only true external is **racingpost.com**, abstracted by `IHtmlLoader` (raw HTML) and the higher-level `IRacingDataDownloader` (URL enumeration + parsed `RaceResult` / `RaceCard`). `MockRacingDataDownloader` is the test mock; `MockHttpMessageHandler` from `RichardSzalay.MockHttp` is used for tests that need to drive the HTTP layer directly. Note the project memory: plain HTTP gets 429-blocked, so production uses Puppeteer.

## Testing Strategy

The core principle: **replace, don't layer.**

- Old unit tests on shallow modules are waste once boundary tests exist — delete them
- Write new tests at the deepened module's interface boundary (typically a command handler's `RunAsync` or a parser's `Parse`)
- Tests assert on observable outcomes through the public interface (e.g. the CSV content captured by `MockFileSystemBuilder`, or the parsed `RaceResult`), not internal state
- Tests should survive internal refactors — they describe behavior, not implementation
- For the Python stage, the equivalent move is to extract pure DataFrame-in / DataFrame-out functions and test those with pytest against a small fixture CSV; delete tests that asserted on intermediate variables

## Issue Template

<issue-template>

## Problem

Describe the architectural friction:

- Which modules are shallow and tightly coupled (cite file paths under `RacePredictor.Core/`, `RaceDataDownloader/`, or `Data/`)
- What integration risk exists in the seams between them (e.g. CSV schema, parser/downloader handshake)
- Why this makes the codebase harder to navigate and maintain

## Proposed Interface

The chosen interface design:

- Interface signature (C# `interface`, abstract class, or Python ABC — types, methods, params)
- Usage example showing how callers use it (which command handler / which Python script)
- What complexity it hides internally

## Dependency Strategy

Which category applies and how dependencies are handled:

- **In-process**: merged directly (e.g. fold helper into parser)
- **Local-substitutable**: tested with `IFileSystem`/`IClock` stand-ins via `MockFileSystemBuilder` / `Substitute.For<IClock>()`
- **Ports & adapters**: port definition, production adapter (Puppeteer/HTTP), test adapter (string fixture)
- **Mock**: mock boundary for racingpost.com via `IHtmlLoader` or `IRacingDataDownloader`

## Testing Strategy

- **New boundary tests to write**: describe the behaviors to verify at the interface (e.g. "Verify the CSV written for a backfilled month")
- **Old tests to delete**: list the shallow module tests that become redundant
- **Test environment needs**: any fixtures (`FakeData.*`), verified snapshots, or pytest fixture CSVs required

## Implementation Recommendations

Durable architectural guidance that is NOT coupled to current file paths:

- What the module should own (responsibilities)
- What it should hide (implementation details)
- What it should expose (the interface contract)
- How callers should migrate to the new interface

</issue-template>
