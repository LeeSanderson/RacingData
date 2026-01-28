using System.Globalization;
using System.IO.Abstractions;
using System.Net;
using CommandLine;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using RaceDataDownloader;
using RaceDataDownloader.Commands.DedupeResults;
using RaceDataDownloader.Commands.DownloadRaceCards;
using RaceDataDownloader.Commands.DownloadResults;
using RaceDataDownloader.Commands.DownloadTodaysRaceCards;
using RaceDataDownloader.Commands.UpdateResults;
using RaceDataDownloader.Commands.ValidateRaceCardPredictions;
using Serilog;
using Serilog.Events;
using Serilog.Extensions.Logging;

var loggerConfiguration = new LoggerConfiguration()
    .MinimumLevel.Is(LogEventLevel.Verbose)
    .WriteTo.Console(formatProvider: CultureInfo.InvariantCulture);

Log.Logger = loggerConfiguration.CreateLogger();
var loggerFactory = new SerilogLoggerFactory();

var serviceCollection = new ServiceCollection();
serviceCollection.AddSingleton<CookieContainer>();
serviceCollection.AddHttpClient().ConfigureHttpClientDefaults(builder =>
{
    builder.ConfigurePrimaryHttpMessageHandler(sp => new SocketsHttpHandler
    {
        UseCookies = true,
        CookieContainer = sp.GetRequiredService<CookieContainer>()
    });
});
var serviceProvider = serviceCollection.BuildServiceProvider();
var httpClientFactory = serviceProvider.GetRequiredService<IHttpClientFactory>();
var cookieContainer = serviceProvider.GetRequiredService<CookieContainer>();

// Add a dummy token cookie to avoid 406 responses
var uri = new Uri("https://www.racingpost.com");
var tokenName = $"CognitoIdentityServiceProvider.3fii107m4bmtggnm21pud2es21.{Guid.NewGuid():N}%40gmail.com.accessToken";
var tokenValue = $"ey{Guid.NewGuid():N}{Guid.NewGuid():N}{Guid.NewGuid():N}{Guid.NewGuid():N}{Guid.NewGuid():N}{Guid.NewGuid():N}{Guid.NewGuid():N}2V1LXdlc3QtMV9iQzBOenlpS2oiLCJjbGllbnRfaWQiOiIzZmlpMTA3bTRibXRnZ25tMjFwdWQyZXMyMSIsIm9yaWdpbl9qdGkiOiIzZTIwNjBkMi0xMDkwLTQyNjUtODhiYi1kMmNjYTNhMDZjYzciLCJldmVudF9pZCI6IjMyMzQ2YTg5LTk0YzktNGQ4Yy1hNTA4LTM3NjNiOTFjZDhkOSIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXdzLmNvZ25pdG8uc2lnbmluLnVzZXIuYWRtaW4iLCJhdXRoX3RpbWUiOjE3Njk1MjM0NjIsImV4cCI6MTc2OTUyNTI2MiwiaWF0IjoxNzY5NTIzNDYyLCJqdGkiOiJiMjE3ZTZiNC1hMTdhLTQzMGItODQ0Ni0xMWU5MmFmMTA0MjciLCJ1c2VybmFtZSI6IjEyNzUzNDE0LWMwMDEtNzBkMS0yZTYzLTdkMzc2OGVjNjFmMSJ9.D1q50MmumQerxmcpCcnCx0CA63gyIp1WN36DAeUAxTTOAGX23klwdAVEjYVOjgjZq0HwmBBgbqN6ohhd1vV18eCzCmGtljzRRiEamHO5TKygalIVRXyrrB67mD03vox0aIiLefb4A4Urr-HtJIYPChjczw9IVFnWZwgOM7k-gwkW8cGVs5qVO3czIKV8t8N53-aJhPO4qkQuJKQumJmI2_j6HMKt7Dj2h7avG3nfsNLHsD0dD_nwU6yg6JR5VH58GP48tf5wHsQrxal0viHzkNZufWDvgDiVnXrHyzjfu1-X6MDs1FpkeOSOUkn1PHKz6NYyC44Jf9G3Ts2XqXakbQ";
cookieContainer.Add(uri, new Cookie(tokenName, tokenValue));


return await Parser.Default.ParseArguments<
        DownloadResultsOptions,
        DownloadRaceCardsOptions,
        UpdateResultsOptions,
        DownloadTodaysRaceCardsOptions,
        ValidateRaceCardPredictionsOptions,
        DedupeResultsOptions>(args)
    .MapResult(
        (DownloadResultsOptions options) => CreateDownloadResultsCommandHandler().RunAsync(options),
        (DownloadRaceCardsOptions options) => CreateDownloadRaceCardsCommandHandler().RunAsync(options),
        (UpdateResultsOptions options) => CreateUpdateResultsCommandHandler().RunAsync(options),
        (DownloadTodaysRaceCardsOptions options) => CreateDownloadTodaysRaceCardsCommandHandler().RunAsync(options),
        (ValidateRaceCardPredictionsOptions options) => CreateValidateRaceCardPredictionsCommandHandler().RunAsync(options),
        (DedupeResultsOptions options) => CreateDedupeResultsCommandHandler().RunAsync(options),
        _ => Task.FromResult(ExitCodes.Error));

DownloadResultsCommandHandler CreateDownloadResultsCommandHandler() =>
    new(new FileSystem(), httpClientFactory, new RealClock(), loggerFactory.CreateLogger<DownloadResultsCommandHandler>());

DownloadRaceCardsCommandHandler CreateDownloadRaceCardsCommandHandler() =>
    new(new FileSystem(), httpClientFactory, new RealClock(), loggerFactory.CreateLogger<DownloadRaceCardsCommandHandler>());

UpdateResultsCommandHandler CreateUpdateResultsCommandHandler() =>
    new(new FileSystem(), httpClientFactory, new RealClock(), loggerFactory.CreateLogger<UpdateResultsCommandHandler>());

DownloadTodaysRaceCardsCommandHandler CreateDownloadTodaysRaceCardsCommandHandler() =>
    new(new FileSystem(), httpClientFactory, new RealClock(), loggerFactory.CreateLogger<DownloadTodaysRaceCardsCommandHandler>());

ValidateRaceCardPredictionsCommandHandler CreateValidateRaceCardPredictionsCommandHandler() =>
    new(new FileSystem(), loggerFactory.CreateLogger<ValidateRaceCardPredictionsCommandHandler>());

DedupeResultsCommandHandler CreateDedupeResultsCommandHandler() =>
    new(new FileSystem(), loggerFactory.CreateLogger<DedupeResultsCommandHandler>());
