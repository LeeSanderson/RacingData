using System.IO.Abstractions;
using NSubstitute;

namespace RaceDataDownloader.Tests;

internal class MockFileSystemBuilder
{
    public const string OutputDirectory = @"c:\out";
    private const string SavedRaceCardsAsJsonFileName = @"c:\out\RaceCards.json";
    private const string SavedRaceCardsAsCsvFileName = @"c:\out\RaceCards.csv";
    private const string SavedResultsAsJsonFileName = @"c:\out\Results.json";
    private const string SavedResultsAsCsvFileName = @"c:\out\Results.csv";
    private const string TodaysSavedResultsAsCsvFileName = @"c:\out\TodaysRaceCards.csv";

    private readonly Dictionary<string, string?> _content = new();

    public IFileSystem FileSystem { get; }
    public string? SavedRaceCardsAsJson => GetContent(SavedRaceCardsAsJsonFileName);
    public string? SavedRaceCardsAsCsv => GetContent(SavedRaceCardsAsCsvFileName);
    public string? SavedResultsAsJson => GetContent(SavedResultsAsJsonFileName);
    public string? SavedResultsAsCsv => GetContent(SavedResultsAsCsvFileName);
    public string? TodaysSavedResultsAsCsv => GetContent(TodaysSavedResultsAsCsvFileName);
    public string? GetContent(string fileName) => _content.GetValueOrDefault(fileName);

    public MockFileSystemBuilder()
    {
        FileSystem = Substitute.For<IFileSystem>();


        FileSystem.File
            .When(x => x.WriteAllTextAsync(Arg.Any<string>(), Arg.Any<string?>()))
            .Do(args =>
            {
                var fileName = args.ArgAt<string>(0);
                var content = args.ArgAt<string?>(1);
                _content[fileName] = content;
            });

        FileSystem.Directory.Exists(OutputDirectory).Returns(true);
    }
}
