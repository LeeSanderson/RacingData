using System.IO.Abstractions;
using CommandLine;
using Microsoft.Extensions.DependencyInjection;
using RaceDataDownloader;
using Serilog;
using Serilog.Events;
using Serilog.Extensions.Logging;
using Microsoft.Extensions.Logging;

var loggerConfiguration = new LoggerConfiguration()
    .MinimumLevel.Is(LogEventLevel.Verbose)
    .WriteTo.Console();

Log.Logger = loggerConfiguration.CreateLogger();
var loggerFactory = new SerilogLoggerFactory();

var serviceCollection = new ServiceCollection();
serviceCollection.AddHttpClient();
var serviceProvider = serviceCollection.BuildServiceProvider();
var httpClientFactory = serviceProvider.GetRequiredService<IHttpClientFactory>();

await Parser.Default.ParseArguments<DownloadResultsOptions>(args)
    .MapResult(
        options => CreateDownloadResultsCommandHandler().RunAsync(options),
        _ => Task.FromResult(ExitCodes.Error));

DownloadResultsCommandHandler CreateDownloadResultsCommandHandler() => 
    new(new FileSystem(), httpClientFactory, loggerFactory.CreateLogger<DownloadResultsCommandHandler>());