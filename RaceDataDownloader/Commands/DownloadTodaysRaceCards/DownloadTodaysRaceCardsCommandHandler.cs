using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using RacePredictor.Core.RacingPost;

namespace RaceDataDownloader.Commands.DownloadTodaysRaceCards;

public class DownloadTodaysRaceCardsCommandHandler : FileCommandHandlerBase<DownloadTodaysRaceCardsCommandHandler, DownloadTodaysRaceCardsOptions>
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly IClock _clock;

    public DownloadTodaysRaceCardsCommandHandler(
        IFileSystem fileSystem,
        IHttpClientFactory httpClientFactory,
        IClock clock,
        ILogger<DownloadTodaysRaceCardsCommandHandler> logger) : base(fileSystem, logger)
    {
        _httpClientFactory = httpClientFactory;
        _clock = clock;
    }

    protected override async Task InternalRunAsync(DownloadTodaysRaceCardsOptions options)
    {
        throw new NotImplementedException();
    }
}