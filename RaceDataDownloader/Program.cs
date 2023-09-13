using System.IO.Abstractions;
using CommandLine;
using Microsoft.Extensions.DependencyInjection;
using RaceDataDownloader;
using Serilog;
using Serilog.Events;
using Serilog.Extensions.Logging;
using Microsoft.Extensions.Logging;
using RaceDataDownloader.Commands.DedupeResults;
using RaceDataDownloader.Commands.DownloadRaceCards;
using RaceDataDownloader.Commands.DownloadResults;
using RaceDataDownloader.Commands.DownloadTodaysRaceCards;
using RaceDataDownloader.Commands.PredictTodaysRaceCards;
using RaceDataDownloader.Commands.PredictTodaysRaceCards.Algorithms;
using RaceDataDownloader.Commands.UpdateResults;
using RaceDataDownloader.Commands.ValidateRaceCardPredictions;

var loggerConfiguration = new LoggerConfiguration()
    .MinimumLevel.Is(LogEventLevel.Verbose)
    .WriteTo.Console();

Log.Logger = loggerConfiguration.CreateLogger();
var loggerFactory = new SerilogLoggerFactory();

var serviceCollection = new ServiceCollection();
serviceCollection.AddHttpClient();
var serviceProvider = serviceCollection.BuildServiceProvider();
var httpClientFactory = serviceProvider.GetRequiredService<IHttpClientFactory>();

await Parser.Default.ParseArguments<
        DownloadResultsOptions,
        DownloadRaceCardsOptions,
        UpdateResultsOptions,
        DownloadTodaysRaceCardsOptions,
        PredictTodaysRaceCardsOptions,
        ValidateRaceCardPredictionsOptions,
        DedupeResultsOptions>(args)
    .MapResult(
        (DownloadResultsOptions options) => CreateDownloadResultsCommandHandler().RunAsync(options),
        (DownloadRaceCardsOptions options) => CreateDownloadRaceCardsCommandHandler().RunAsync(options),
        (UpdateResultsOptions options) => CreateUpdateResultsCommandHandler().RunAsync(options),
        (DownloadTodaysRaceCardsOptions options) => CreateDownloadTodaysRaceCardsCommandHandler().RunAsync(options),
        (PredictTodaysRaceCardsOptions options) => CreatePredictTodaysRaceCardsCommandHandler().RunAsync(options),
        (ValidateRaceCardPredictionsOptions options) => CreateValidateRaceCardPredictionsCommandHandler().RunAsync(options),
        (DedupeResultsOptions options) => CreateDedupeResultsCommandHandler().RunAsync(options),
        _ => Task.FromResult(ExitCodes.Error));

DownloadResultsCommandHandler CreateDownloadResultsCommandHandler() => 
    new(new FileSystem(), httpClientFactory, new RealClock(),  loggerFactory.CreateLogger<DownloadResultsCommandHandler>());

DownloadRaceCardsCommandHandler CreateDownloadRaceCardsCommandHandler() =>
    new(new FileSystem(), httpClientFactory, new RealClock(), loggerFactory.CreateLogger<DownloadRaceCardsCommandHandler>());

UpdateResultsCommandHandler CreateUpdateResultsCommandHandler() =>
    new(new FileSystem(), httpClientFactory, new RealClock(), loggerFactory.CreateLogger<UpdateResultsCommandHandler>());

DownloadTodaysRaceCardsCommandHandler CreateDownloadTodaysRaceCardsCommandHandler() =>
    new(new FileSystem(), httpClientFactory, new RealClock(), loggerFactory.CreateLogger<DownloadTodaysRaceCardsCommandHandler>());

PredictTodaysRaceCardsCommandHandler CreatePredictTodaysRaceCardsCommandHandler()
{
    var racePredictorFactory = new RacePredictorFactory();
    // TODO: Register algorithms here
    return new(new FileSystem(), racePredictorFactory, loggerFactory.CreateLogger<PredictTodaysRaceCardsCommandHandler>());
}

ValidateRaceCardPredictionsCommandHandler CreateValidateRaceCardPredictionsCommandHandler() =>
    new(new FileSystem(), loggerFactory.CreateLogger<ValidateRaceCardPredictionsCommandHandler>());

DedupeResultsCommandHandler CreateDedupeResultsCommandHandler() =>
    new(new FileSystem(), loggerFactory.CreateLogger<DedupeResultsCommandHandler>());
