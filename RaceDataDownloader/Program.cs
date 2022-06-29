using System.IO.Abstractions;
using CommandLine;
using Microsoft.Extensions.DependencyInjection;
using RaceDataDownloader;
using Serilog;
using Serilog.Events;
using Serilog.Extensions.Logging;
using Microsoft.Extensions.Logging;
using RaceDataDownloader.Commands.DownloadRaceCards;
using RaceDataDownloader.Commands.DownloadResults;
using RaceDataDownloader.Commands.UpdateResults;

var loggerConfiguration = new LoggerConfiguration()
    .MinimumLevel.Is(LogEventLevel.Verbose)
    .WriteTo.Console();

Log.Logger = loggerConfiguration.CreateLogger();
var loggerFactory = new SerilogLoggerFactory();

var serviceCollection = new ServiceCollection();
serviceCollection.AddHttpClient();
var serviceProvider = serviceCollection.BuildServiceProvider();
var httpClientFactory = serviceProvider.GetRequiredService<IHttpClientFactory>();

await Parser.Default.ParseArguments
        <DownloadResultsOptions, 
            DownloadRaceCardsOptions, 
            UpdateResultsOptions>(args)
    .MapResult(
        (DownloadResultsOptions downloadResultsOptions)  => CreateDownloadResultsCommandHandler().RunAsync(downloadResultsOptions),
        (DownloadRaceCardsOptions downloadRaceCardsOptions) => CreateDownloadRaceCardsCommandHandler().RunAsync(downloadRaceCardsOptions),
        (UpdateResultsOptions updateResultsOptions) => CreateUpdateResultsCommandHandler().RunAsync(updateResultsOptions),
        _ => Task.FromResult(ExitCodes.Error));

DownloadResultsCommandHandler CreateDownloadResultsCommandHandler() => 
    new(new FileSystem(), httpClientFactory, new RealClock(),  loggerFactory.CreateLogger<DownloadResultsCommandHandler>());

DownloadRaceCardsCommandHandler CreateDownloadRaceCardsCommandHandler() =>
    new(new FileSystem(), httpClientFactory, new RealClock(), loggerFactory.CreateLogger<DownloadRaceCardsCommandHandler>());

UpdateResultsCommandHandler CreateUpdateResultsCommandHandler() =>
    new(new FileSystem(), httpClientFactory, new RealClock(), loggerFactory.CreateLogger<UpdateResultsCommandHandler>());
