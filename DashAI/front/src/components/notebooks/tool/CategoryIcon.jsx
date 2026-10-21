import React from "react";
import TableChartIcon from "@mui/icons-material/TableChart";
import BarChartIcon from "@mui/icons-material/BarChart";
import ScatterPlotIcon from "@mui/icons-material/ScatterPlot";
import TimelineIcon from "@mui/icons-material/Timeline";
import FunctionsIcon from "@mui/icons-material/Functions";
import BuildIcon from "@mui/icons-material/Build";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import DnsIcon from "@mui/icons-material/Dns";
import LayersIcon from "@mui/icons-material/Layers";
import FilterListIcon from "@mui/icons-material/FilterList";
import CasinoIcon from "@mui/icons-material/Casino";
import ExtensionIcon from "@mui/icons-material/Extension";
import PsychologyIcon from "@mui/icons-material/Psychology";
import DescriptionIcon from "@mui/icons-material/Description";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";

const ICONS = {
  TableChart: TableChartIcon,
  BarChart: BarChartIcon,
  ScatterPlot: ScatterPlotIcon,
  Timeline: TimelineIcon,
  Functions: FunctionsIcon,
  Build: BuildIcon,
  TrendingUp: TrendingUpIcon,
  Dns: DnsIcon,
  Layers: LayersIcon,
  FilterList: FilterListIcon,
  Casino: CasinoIcon,
  Psychology: PsychologyIcon,
  Description: DescriptionIcon,
  TextSnippet: TextSnippetIcon,
  Extension: ExtensionIcon,
};

const DEFAULT_ICON = ExtensionIcon;

/**
 * Renders an icon component for a given category.
 *
 * @param {Object} props - Component props.
 * @param {string} props.icon - Icon key used to look up an icon component in the chosen icon map.
 * @param {string} [props.color] - CSS color applied to the rendered icon.
 * @returns {JSX.Element} The selected icon component rendered with inline style { color, fontSize: 30 }.
 *
 * @remarks
 * - Falls back to DEFAULT_ICON if the category key is not found in the selected map.
 * - Depends on CONVERTER_CATEGORY_ICONS, EXPLORER_CATEGORY_ICONS, and DEFAULT_ICON being defined in scope.
 */
export function CategoryIcon({ icon, color }) {
  const IconComponent = ICONS[icon] || ICONS.Extension;
  return <IconComponent style={{ color: color ?? "white", fontSize: 30 }} />;
}
