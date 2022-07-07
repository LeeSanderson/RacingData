using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using RacePredictor.Core.RacingPost;

namespace RaceDataDownloader.Commands.DownloadTodaysRaceCards;

public class DownloadTodaysRaceCardsCommandHandler : FileCommandHandlerBase
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly IClock _clock;
    private readonly ILogger<DownloadTodaysRaceCardsCommandHandler> _logger;

    public DownloadTodaysRaceCardsCommandHandler(
        IFileSystem fileSystem,
        IHttpClientFactory httpClientFactory,
        IClock clock,
        ILogger<DownloadTodaysRaceCardsCommandHandler> logger) : base(fileSystem)
    {
        _httpClientFactory = httpClientFactory;
        _clock = clock;
        _logger = logger;
    }

    public async Task<int> RunAsync(DownloadTodaysRaceCardsOptions options)
    {
        throw new NotImplementedException();
    }
}