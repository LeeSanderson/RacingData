using System.IO.Abstractions;
using Microsoft.Extensions.Logging;
using RacePredictor.Core.RacingPost;

namespace RaceDataDownloader.Commands.UpdateResults;

public class UpdateResultsCommandHandler : FileCommandHandlerBase
{
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly IClock _clock;
    private readonly ILogger<UpdateResultsCommandHandler> _logger;

    public UpdateResultsCommandHandler(
        IFileSystem fileSystem,
        IHttpClientFactory httpClientFactory,
        IClock clock,
        ILogger<UpdateResultsCommandHandler> logger) : base(fileSystem)
    {
        _httpClientFactory = httpClientFactory;
        _clock = clock;
        _logger = logger;
    }

    public async Task<int> RunAsync(UpdateResultsOptions options)
    {
        throw new NotImplementedException();
    }
}