using Microsoft.Extensions.Logging;
using Xunit.Abstractions;

namespace RaceDataDownloader.Tests;

// Like OutputLogger, but keeps the entries so a test can assert on what was logged (e.g. a warning).
public class RecordingLogger<T>(ITestOutputHelper output) : ILogger<T>
{
    public List<(LogLevel Level, string Message)> Entries { get; } = new();

    public void Log<TState>(LogLevel logLevel, EventId eventId, TState state, Exception? exception, Func<TState, Exception?, string> formatter)
    {
        var message = formatter(state, exception);
        Entries.Add((logLevel, message));
        output.WriteLine($"[{logLevel}] {message}");
        if (exception != null)
        {
            output.WriteLine(exception.ToString());
        }
    }

    public bool IsEnabled(LogLevel logLevel) => true;

    public IDisposable BeginScope<TState>(TState state) where TState : notnull => DoesNothingWhenDisposed.Instance;

    private sealed class DoesNothingWhenDisposed : IDisposable
    {
        public static readonly IDisposable Instance = new DoesNothingWhenDisposed();

        public void Dispose()
        {
        }
    }
}
