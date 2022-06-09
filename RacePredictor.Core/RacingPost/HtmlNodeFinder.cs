using HtmlAgilityPack;

namespace RacePredictor.Core.RacingPost;

public class HtmlNodeFinder : HtmlNodeFinder<HtmlNodeFinder>
{
    private readonly HtmlOptionalNodeFinder _optional;

    public HtmlNodeFinder(HtmlNode node) : base(node)
    {
        _optional = new HtmlOptionalNodeFinder(node);
    }

    public HtmlNode GetNode()
    {
        var currentQuery = XPathQuery;
        return InternalGetOptionalNode() ?? throw new Exception($"Unable to find element for XPATH '{currentQuery}'");
    }

    public HtmlNode[] GetNodes()
    { 
        var currentQuery = XPathQuery;
        return InternalGetOptionalNodes() ?? throw new Exception($"Unable to find element for XPATH '{currentQuery}'");
    }

    public string GetAttribute(string attributeName, string defaultValue = "") => GetNode().GetAttributeValue(attributeName, defaultValue);

    public string GetText() => GetNode().InnerText.TrimAllWhiteSpace();

    public string GetDirectText() => GetNode().GetDirectInnerText().TrimAllWhiteSpace();

    public IEnumerable<string> GetTexts() => GetNodes().Select(s => s.InnerText.TrimAllWhiteSpace());

    public IEnumerable<string> GetDirectTexts() => GetNodes().Select(s => s.GetDirectInnerText().TrimAllWhiteSpace());

    public int[] GetIntegers() => GetNodes().Select(s => s.InnerText.TrimAllWhiteSpace().AsInt()).ToArray();

    public HtmlOptionalNodeFinder Optional() => _optional;
}

public class HtmlOptionalNodeFinder : HtmlNodeFinder<HtmlOptionalNodeFinder>
{
    public HtmlOptionalNodeFinder(HtmlNode node) : base(node)
    {
    }

    public HtmlNode? GetNode() => InternalGetOptionalNode();

    public HtmlNode[]? GetNodes() => InternalGetOptionalNodes();

    public string? GetAttribute(string attributeName, string? defaultValue = null) => GetNode()?.GetAttributeValue(attributeName, defaultValue) ?? defaultValue;

    public string? GetText() => GetNode()?.InnerText?.TrimAllWhiteSpace().NullIfEmpty();
}

public class HtmlNodeFinder<THtmlNodeFinder>
    where THtmlNodeFinder : HtmlNodeFinder<THtmlNodeFinder>
{
    private readonly HtmlNode _node;
    private string _pathQuery = "//*";
    private string? _subQuery;
    private readonly bool _relative;

    public HtmlNodeFinder(HtmlNode node)
    {
        _node = node;
        _relative = _node != _node.OwnerDocument.DocumentNode;
    }

    protected string XPathQuery => (_relative ? "." : "") + _pathQuery + (_subQuery ?? string.Empty);

    public THtmlNodeFinder Element(string tagName)
    {
        _pathQuery = "//" + tagName;
        return (THtmlNodeFinder)this;
    }

    public THtmlNodeFinder Span() => Element("span");

    public THtmlNodeFinder Div() => Element("div");

    public THtmlNodeFinder Anchor() => Element("a");

    public THtmlNodeFinder TableCell() => Element("td");

    public THtmlNodeFinder AnyElement() => Element("*");

    public THtmlNodeFinder WithAttribute(string attributeName, string attributeValue)
    {
        _subQuery = $"[@{attributeName}='{attributeValue}']";
        return (THtmlNodeFinder)this;
    }

    public THtmlNodeFinder WithCssClass(string classValue)
    {
        _subQuery = $"[contains(@class, '{classValue}')]";
        return (THtmlNodeFinder)this;
    }

    public THtmlNodeFinder WithSelector(string selectorValue)
    {
        _subQuery = $"[@data-test-selector='{selectorValue}']";
        return (THtmlNodeFinder)this;
    }

    public THtmlNodeFinder WithDataEnding(string dataValue)
    {
        _subQuery = $"[@data-ending='{dataValue}']";
        return (THtmlNodeFinder)this;
    }

    public THtmlNodeFinder Reset()
    {
        _subQuery = null;
        return AnyElement();
    }

    protected HtmlNode? InternalGetOptionalNode()
    {
        var node = _node.SelectSingleNode(XPathQuery);
        Reset();
        return node;
    }

    protected HtmlNode[]? InternalGetOptionalNodes()
    {
        var nodes = _node.SelectNodes(XPathQuery);
        Reset();
        return nodes?.ToArray();
    }
}
