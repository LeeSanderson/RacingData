using PuppeteerSharp;
using PuppeteerSharp.Mobile;

namespace RacePredictor.Core.RacingPost;

public class PuppeteerHtmlLoader : IHtmlLoader
{
    private const int DefaultTimeoutMilliseconds = 360_000;
    private static readonly SemaphoreSlim BrowserFetcherSemaphore = new(1, 1);

    public async Task<string> GetHtmlResponseFrom(string url)
    {
        await EnsureBrowserDownloaded();
        await using var browser = await Puppeteer.LaunchAsync(new LaunchOptions
        {
            Headless = true,
            Args = ["--no-sandbox", "--disable-setuid-sandbox"],
            Timeout = DefaultTimeoutMilliseconds,
            ProtocolTimeout = DefaultTimeoutMilliseconds
        });

        var page = await browser.NewPageAsync();
        page.DefaultTimeout = DefaultTimeoutMilliseconds;
        page.DefaultNavigationTimeout = DefaultTimeoutMilliseconds;
        var device = Puppeteer.Devices[DeviceDescriptorName.IPadLandscape];
        await page.EmulateAsync(device);

        var response = await page.GoToAsync(url);
        if (!response.Ok)
        {
            throw new Exception($"Failed to load url {url} with status code {response.Status}");
        }

        return await page.GetContentAsync();
    }

    private static async Task EnsureBrowserDownloaded()
    {
        // We need to fetch it
        await BrowserFetcherSemaphore.WaitAsync();
        try
        {
            var browserFetcher = new BrowserFetcher();
            await browserFetcher.DownloadAsync();
        }
        finally
        {
            BrowserFetcherSemaphore.Release();
        }
    }
}
