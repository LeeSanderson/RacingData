using Microsoft.Extensions.Logging;
using Xunit.Abstractions;

namespace RaceDataDownloader.Tests;

public class OutputLogger<T>(ITestOutputHelper output) : ILogger<T>
{
    public void Log<TState>(LogLevel logLevel, EventId eventId, TState state, Exception? exception, Func<TState, Exception?, string> formatter)
    {
        output.WriteLine(formatter(state, exception));
        if (exception != null)
        {
            output.WriteLine(exception.ToString());
        }
    }

    public bool IsEnabled(LogLevel logLevel) => true;

    public IDisposable BeginScope<TState>(TState state) where TState : notnull => DoesNothingWhenDisposed.Instance;

    private class DoesNothingWhenDisposed : IDisposable
    {
        public static readonly IDisposable Instance = new DoesNothingWhenDisposed();

        public void Dispose()
        {
        }
    }
}
