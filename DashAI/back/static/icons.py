from enum import Enum


class Icon(str, Enum):
    """
    Enum class for available icons in DashAI.
    """

    # Explorer
    TableChart = "TableChart"
    BarChart = "BarChart"
    ScatterPlot = "ScatterPlot"
    Timeline = "Timeline"
    Functions = "Functions"
    TextSnippet = "TextSnippet"

    # Converter
    Build = "Build"
    Dns = "Dns"
    TrendingUp = "TrendingUp"
    Layers = "Layers"
    FilterList = "FilterList"
    Casino = "Casino"
    Psychology = "Psychology"
    Description = "Description"

    # Fallback
    Extension = "Extension"
