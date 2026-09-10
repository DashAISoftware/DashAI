/**
 * Traces whose axis labels sit along the top of the plot domain, where a
 * figure title would otherwise be drawn.
 */
const TOP_LABEL_TRACE_TYPES = ["parcoords", "parcats"];

function hasTopLabelTrace(data) {
  return (
    Array.isArray(data) &&
    data.some((trace) => TOP_LABEL_TRACE_TYPES.includes(trace?.type))
  );
}

function hasTitle(layout) {
  const title = layout?.title;
  const text = typeof title === "string" ? title : title?.text;
  return typeof text === "string" && text.trim().length > 0;
}

/**
 * Build the default plot margin for {@link PlotlyJsonVisualizer}.
 *
 * A titled parallel coordinates or categories figure gets extra top room: its
 * dimension labels are drawn along the top of the plot domain, in the same
 * band as the title, so the standard top margin would let them overlap.
 *
 * @param {object} plotData The parsed `{data, layout}` figure.
 * @param {boolean} minimalist Whether the compact card preview is rendering.
 * @returns {{l: number, r: number, t: number, b: number}} The base margin,
 *   before any figure-supplied margin is spread over it.
 */
export function buildPlotMargin(plotData, minimalist) {
  if (minimalist) return { l: 40, r: 20, t: 30, b: 40 };
  const t =
    hasTopLabelTrace(plotData?.data) && hasTitle(plotData?.layout) ? 90 : 50;
  return { l: 60, r: 30, t, b: 60 };
}
