using Microsoft.Extensions.Logging;
using Xunit.Abstractions;

namespace RaceDataDownloader.Tests;

public class OutputLogger<T> : ILogger<T>
{
    private readonly ITestOutputHelper _output;

    public OutputLogger(ITestOutputHelper output)
    {
        _output = output;
    }

    public void Log<TState>(LogLevel logLevel, EventId eventId, TState state, Exception? exception, Func<TState, Exception?, string> formatter)
    {
        _output.WriteLine(formatter(state, exception));
    }

    public bool IsEnabled(LogLevel logLevel)
    {
        return true;
    }

    public IDisposable BeginScope<TState>(TState state)
    {
        return DoesNothingWhenDisposed.Instance;
    }

    private class DoesNothingWhenDisposed : IDisposable
    {
        public static readonly IDisposable Instance = new DoesNothingWhenDisposed();

        public void Dispose()
        {
        }
    }
}